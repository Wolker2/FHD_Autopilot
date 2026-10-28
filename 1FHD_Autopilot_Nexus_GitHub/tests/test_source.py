from pathlib import Path
import hashlib,json,shutil,subprocess,sys,tempfile,unittest,zipfile

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from build import compile_source,resource_audit,load,SCRIPT_NAME
from scr_codec import encode as encode_scr
from gi_codec import encode as encode_gi,decode as decode_gi
from inspect_scr import parse

class SourceTests(unittest.TestCase):
    def test_all_file_hashes_and_resource_references(self):
        files,configs=compile_source();expected=load(ROOT/'original-file-sha256.json')
        self.assertEqual({k:hashlib.sha256(v).hexdigest()for k,v in files.items()},expected)
        self.assertEqual(len(files),31)
        self.assertEqual(resource_audit(files,configs),{'cache_references_checked':26,'missing':[]})
        for path in(ROOT/'source/DATA/UI').glob('*.json'):
            tree=load(path);self.assertEqual(decode_gi(encode_gi(tree)),tree,path.name)

    def test_controller_edit_rebuilds_offset_and_preserves_definitions(self):
        source=ROOT/'source/script';scene=load(source/(SCRIPT_NAME+'.rson'));layout=load(source/(SCRIPT_NAME+'.layout.json'))
        for group in scene['Visual.Objects']:
            for item in group.get('Operations',[]):
                if item['Name']=='global_code':item['Code'].insert(0,'// source edit test')
        data=encode_scr(scene,layout)
        with tempfile.TemporaryDirectory()as folder:
            path=Path(folder)/'controller.scr';path.write_bytes(data);model=parse(path)
        self.assertGreater(model['local_offset'],28)
        self.assertTrue(model['global_code'].startswith('// source edit test\n'))
        self.assertEqual(len(model['local_variables']),4)
        self.assertEqual([d['name']for d in model['dialogs']],['SkipIncoming'])

    def test_embedded_dat_code_is_an_active_source_input(self):
        original,_=compile_source()
        with tempfile.TemporaryDirectory()as folder:
            target=Path(folder);shutil.copytree(ROOT/'source',target/'source')
            path=target/'source/CFG/Rus/Lang.json';data=load(path);block=data['root']
            for name in ['Script','FHDAutopilot','AfterStep']:
                block=next(e['value']for e in block['entries']if e['kind']=='block'and e['name']==name)
            parameter=next(e for e in block['entries']if e['kind']=='parameter')
            parameter['value']+=' // source edit test'
            path.write_text(json.dumps(data,ensure_ascii=False),encoding='utf-8')
            files,_=compile_source(target)
        self.assertEqual([k for k in files if files[k]!=original[k]],['CFG/Rus/Lang.dat'])

    def test_source_only_build_has_no_prebuilt_dependencies(self):
        with tempfile.TemporaryDirectory()as folder:
            target=Path(folder)
            for name in ['scripts','source']:shutil.copytree(ROOT/name,target/name,ignore=shutil.ignore_patterns('__pycache__'))
            shutil.copy2(ROOT/'original-file-sha256.json',target/'original-file-sha256.json')
            self.assertFalse(any(p.suffix in('.dat','.scr','.gi','.dll')for p in target.rglob('*')if p.is_file()))
            result=subprocess.run([sys.executable,str(target/'scripts/build.py'),'--strict-original'],cwd=target,capture_output=True,text=True)
            self.assertEqual(result.returncode,0,result.stdout+'\n'+result.stderr)
            expected=load(ROOT/'original-file-sha256.json')
            with zipfile.ZipFile(target/'dist/FHD_Autopilot_FROM_SOURCE.zip')as z:
                self.assertIsNone(z.testzip());self.assertEqual(len(z.namelist()),31)
                for name,digest in expected.items():
                    self.assertEqual(hashlib.sha256(z.read('Mods/FHD_MODS/FHD_Autopilot/'+name)).hexdigest(),digest)

if __name__=='__main__':unittest.main()
