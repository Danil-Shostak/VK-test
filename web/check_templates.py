from jinja2 import Environment, FileSystemLoader

env = Environment(loader=FileSystemLoader('templates'))

templates = ['view_profile.html', 'comparison.html', 'result.html']
for tpl in templates:
    try:
        env.get_template(tpl)
        print(f'{tpl}: OK')
    except Exception as e:
        print(f'{tpl}: ERROR - {e}')
