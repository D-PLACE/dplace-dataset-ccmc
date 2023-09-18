from setuptools import setup


setup(
    name='cldfbench_ccmc',
    py_modules=['cldfbench_ccmc'],
    include_package_data=True,
    zip_safe=False,
    entry_points={
        'cldfbench.dataset': [
            'ccmc=cldfbench_ccmc:Dataset',
        ]
    },
    install_requires=[
        'clldutils>=3.20',
        'cldfbench',
    ],
    extras_require={
        'test': [
            'pytest-cldf',
        ],
    },
)
