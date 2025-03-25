import os
from setuptools import setup, find_packages
from setuptools.command.install import install


class CustomInstallCommand(install):
    def run(self):
        os.makedirs('to_scrape/pdfs', exist_ok=True)
        with open('to_scrape/urls_to_scrape.csv', 'w') as f:
            f.write('url\n')

        os.makedirs('logs/', exist_ok=True)
        log_file_path = os.path.join('logs/', 'app_log.log')
        if not os.path.exists(log_file_path):
            with open(log_file_path, 'w') as f:
                pass

        os.makedirs('visited', exist_ok=True)

        install.run(self)


def load_requirements(filename="requirements.txt"):
    with open(filename) as f:
        return f.read().splitlines()


setup(
    name='statutscan-data-scraping',
    packages=find_packages(),
    cmdclass={
        'install': CustomInstallCommand,
    },
    install_requires=load_requirements()
)
