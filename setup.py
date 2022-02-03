from setuptools import setup, find_packages


setup(name="soc_apiclient_remedy",
      version="1.0.0",
      description="SOC Remedy client API",
      author="Jean-Philippe Clipffel",
      packages=["soc", "soc.apiclient", "soc.apiclient.remedy", ],
      namespace_packages = ["soc", "soc.apiclient", ],
      entry_points={"console_scripts": ["soc.apiclient.remedy=soc.apiclient.remedy.__main__:main", ]},
      install_requires=["jinja2", "requests", "argparse", ],
      include_package_data=True
)
