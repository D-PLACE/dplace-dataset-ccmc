# Releasing the CCMC

```shell
cldfbench download cldfbench_ccmc.py
```

```shell
cldfbench makecldf cldfbench_ccmc.py --with-zenodo --with-cldfreadme --glottolog-version v4.8
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
```
