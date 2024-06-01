# kloch_kiche

![python support](https://img.shields.io/badge/Python>=3.7-blue?logo=python&logoColor=yellow)
![linux support](https://img.shields.io/badge/Linux-FCC624?&logo=linux&logoColor=black)
![windows support](https://img.shields.io/badge/Windows-0078D6?&logo=windows&logoColor=white)

Launcher plugin for [Kloch](https://github.com/knotsanimation/kloch) allowing to quickly execute python applications.

kiche create a full python environment from scratch that is discarded on exit:
- download python from https://github.com/indygreg/python-build-standalone
  - (supposed to support all the major os)
- create a virtual environment using [uv](https://github.com/astral-sh/uv)
- install dependencies using [uv](https://github.com/astral-sh/uv)
- activate venv and call python with an arbitrary command

It takes about 11s to complete this process, with the most time being
downloading python and extracting the archive.

## development

```shell
poetry install --extra dev
```

### running tests

```shell
poetry install --extra test
pytest ./tests -s
```