from distutils.command.bdist_dumb import bdist_dumb
from distutils.core import setup


class custom_bdist_dumb(bdist_dumb):

    def reinitialize_command(self, name, **kw):
        cmd = bdist_dumb.reinitialize_command(self, name, **kw)
        if name == 'install':
            cmd.install_lib = '/'
        return cmd


setup(
    name='caaspctl',
    version='1.0',
    packages=[
        'caasp'
    ],
    url='http://github.com/kubic-project/caaspctl',
    py_modules=['__main__'],
    license='BSD',
    entry_points={
        'console_scripts': [
            'caaspctl = caasp.__main__:main'
        ],
        'setuptools.installation': [
            'eggsecutable = caasp.__main__:main',
        ]
    },
    zip_safe=True,
    cmdclass={'bdist_dumb': custom_bdist_dumb},
    author='Alvaro Saurin',
    author_email='alvaro.saurin@suse.com',
    description='A command line client for CaaSP'
)
