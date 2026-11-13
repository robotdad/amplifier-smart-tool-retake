"""Retake content adapter around the unmodified Amplifier Smart Tools theme."""
import argparse
import importlib.util
import json
import shutil
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parent.parent
THEME=ROOT/'site/theme'

def replace_once(text, old, new):
    if text.count(old)!=1:raise ValueError(f'Theme content changed; review Retake adapter: {old[:70]}')
    return text.replace(old,new,1)

def build(output):
    config=json.loads((ROOT/'site/site.json').read_text(encoding='utf-8'))
    sys.path.insert(0,str(THEME))
    spec=importlib.util.spec_from_file_location('family_theme',THEME/'build.py')
    theme=importlib.util.module_from_spec(spec);spec.loader.exec_module(theme)
    # Identity is local product data, not a change to the vendored family registry.
    theme.PAGES[config['key']]=config['identity']
    args=argparse.Namespace(local=False,family_owner=None)
    theme.SPEC=theme.page_url('overview',args)+'spec/'
    body=theme.tool_page(config,args)
    replacements={
      'Bring it to<br>your agent.':'Start with<br>a real scene.',
      'Start with the outcome you want. Your agent can install the tool and use its help to carry out the work.':'The local renderer is available now. Automatic preparation from a remembered scene is the next step, not a feature this page claims is finished.',
      'Help your agent can use.':'A local pipeline, today.',
      'Amplifier Smart Tools provide help in skill format: instructions your agent can read to understand capabilities, inputs, and how to use the tool. Ask your agent to read <code>--help</code> before getting started.':'Read the environment guide and create a scene JSON. The runner generates takes, checks words, mixes protected audio and renders comparison versions. The future smart-tool layer will prepare that scene record for you.'
    }
    for old,new in replacements.items():body=replace_once(body,old,new)
    media=f'<a href="./assets/{Path(config["image"]).name}" aria-label="Open full-size {theme.esc(config["name"])} image"><img src="./assets/{Path(config["image"]).name}" alt="{theme.esc(config["alt"])}" width="{config["width"]}" height="{config["height"]}" fetchpriority="high"></a>'
    animated=f'<img class="retake-identity" src="./assets/{Path(config["image"]).name}" data-motion-src="./assets/{Path(config["animation"]).name}" data-still-src="./assets/{Path(config["image"]).name}" alt="{theme.esc(config["alt"])}" width="{config["width"]}" height="{config["height"]}" fetchpriority="high">'
    body=replace_once(body,media,animated)
    body=replace_once(body,theme.link('./assets/'+Path(config['image']).name,'View full size'),'<button class="motion-toggle" data-motion-toggle hidden type="button" aria-pressed="false">Pause motion</button> '+theme.link('./assets/'+Path(config['image']).name,'Static PNG')+' '+theme.link('./assets/'+Path(config['animation']).name,'Animated GIF'))
    body=replace_once(body,'<section class="section two-col"><div><p class="eyebrow">How it works</p>', '<aside class="retake-status" role="note"><strong>In development.</strong> The local manifest pipeline is implemented. Natural-language discovery, automatic speaker preparation and portable backend profiles are still being built.</aside><section class="section two-col"><div><p class="eyebrow">How it works</p>')
    page=theme.document(config,body,args)
    page=page.replace('<link rel="icon" href="./assets/favicon.svg"','<link rel="icon" href="./assets/retake-mark.svg"')
    page=page.replace('</head>','<link rel="stylesheet" href="./assets/retake.css"><meta property="og:image" content="https://robotdad.github.io/amplifier-smart-tool-retake/assets/retake-static.png"></head>')
    out=Path(output).resolve()
    if out==ROOT or ROOT.is_relative_to(out) or out in [ROOT/'site',THEME]:raise ValueError('Unsafe generated-site output directory')
    (out/'assets').mkdir(parents=True,exist_ok=True)
    for name in ['style.css','site.js']:shutil.copy2(THEME/name,out/'assets'/name)
    shutil.copytree(THEME/'assets',out/'assets',dirs_exist_ok=True)
    for file in (ROOT/'site/assets').iterdir():
        if file.is_file():shutil.copy2(file,out/'assets'/file.name)
    (out/'index.html').write_text(page,encoding='utf-8');(out/'.nojekyll').touch()
    print(f'Built Retake: {out}')
    return out

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',default='_site')
    build(parser.parse_args().output)
