import subprocess
import requests
import shutil
import json
import os
import dtlpy as dl


def bump(bump_type):
    subprocess.run(f'bumpversion {bump_type}', shell=True)
    subprocess.run('git add .', shell=True)
    subprocess.run('git commit -am "Bump version"', shell=True)
    subprocess.run('git push --follow-tags', shell=True)


def build():
    root_path = os.getcwd()
    srcs_path = os.path.join(root_path, 'srcs')
    panels_path = os.path.join(root_path, 'panels')

    for panel_name in os.listdir(srcs_path):
        panel_path = os.path.join(srcs_path, panel_name)
        if not os.path.isfile(os.path.join(panel_path, 'package.json')):
            continue
        print(f'Building panel name: {panel_name}')
        os.chdir(panel_path)
        subprocess.check_call(f'npm i', shell=True)
        subprocess.check_call(f'npm run build', shell=True)
        os.chdir(root_path)

        print(f'Copying dist to panels/{panel_name}')
        src_dir = os.path.join(panel_path, 'dist')
        dst_dir = os.path.join(panels_path, panel_name)
        # clean destination
        if os.path.isdir(dst_dir):
            shutil.rmtree(dst_dir)
        # move dist folder
        shutil.move(src=src_dir, dst=os.path.dirname(dst_dir))
        # rename to panel name
        os.rename(os.path.join(panels_path, 'dist'), os.path.join(panels_path, panel_name))


def publish_and_install(project_id):
    success = True
    env = dl.environment()
    with open('dataloop.json') as f:
        manifest = json.load(f)
    app_name = manifest['name']
    app_version = manifest['version']
    user = os.environ.get('GITHUB_ACTOR', dl.info()['user_email'])
    try:
        if project_id is None:
            raise ValueError("Must input project_id to publish and install")
        print(f'Deploying to env : {dl.environment()}')

        project = dl.projects.get(project_id=project_id)  # DataloopApps

        print(f'publishing to project: {project.name}')

        # publish dpk to app store
        dpk = project.dpks.publish()
        print(f'published successfully! dpk name: {dpk.name}, version: {dpk.version}, dpk id: {dpk.id}')

        try:
            app = project.apps.get(app_name=dpk.display_name)
            print(f'already installed, updating...')
            app.dpk_version = dpk.version
            app.update()
            print(f'update done. app id: {app.id}')
        except dl.exceptions.NotFound:
            print(f'installing ..')

            app = project.apps.install(dpk=dpk, app_name=dpk.display_name)
            print(f'installed! app id: {app.id}')

        print(f'Done!')

    except Exception:
        success = False
    finally:

        status_msg = ':heavy_check_mark: Success :rocket:' if success else ':x: Failure :cry:'

        msg = f"""{status_msg}
        *App*: `{app_name}:{app_version}` => *{env}* by {user}
        """
        webhook = os.environ.get('SLACK_WEBHOOK')
        if webhook is None:
            print('WARNING: SLACK_WEBHOOK is None, cannot report')
        else:
            resp = requests.post(url=webhook,
                                 json=
                                 {
                                     "blocks": [
                                         {
                                             "type": "section",
                                             "text": {
                                                 "type": "mrkdwn",
                                                 "text": msg
                                             }
                                         }

                                     ]
                                 })
            print(resp)


if __name__ == "__main__":
    # parser = argparse.ArgumentParser(description='Build, Bump, Publish and Install')
    # parser.add_argument('--tag', action='store_true', help='Create a version git tag')
    # parser.add_argument('--publish', action='store_true', help='Publish DPK and install app')
    #
    # parser.add_argument('--project', help='Project to publish and install to')
    # parser.add_argument('--bump-type', default='patch', help='Bump version type: "patch"/"prerelease"/"minor"/"major"')
    # args = parser.parse_args()
    #
    # if args.tag is True:
    #     # run build also here to check it works before creating the git tag
    #     build()
    #     # bump and push the new tag
    #     bump(bump_type=args.bump_type)
    #
    # if args.publish is True:
    #     build()
    #     publish_and_install(project_id=args.project)
    build()
    bump(bump_type='patch')
    publish_and_install(project_id='')
