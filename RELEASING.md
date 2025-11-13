# Releasing the CCMC

```shell
cldfbench download cldfbench_ccmc.py
```

```shell
cldfbench makecldf cldfbench_ccmc.py --with-zenodo --with-cldfreadme --glottolog-version v5.2
pytest
```

```shell
cldfbench cldfviz.map cldf --parameters CCMC1 --pacific-centered --format png --width 20 --output map.png --with-ocean
```

```shell
cldferd --format compact.svg cldf > erd.svg
```

```shell
cldfbench readme cldfbench_ccmc.py
cldfbench zenodo --communities dplace cldfbench_ccmc.py
dplace check cldfbench_ccmc.py
```

```shell
git status
git tag
```

Add, commit and push all changes.

```shell
dplace release cldfbench_carneiro4.py vX.Y
```