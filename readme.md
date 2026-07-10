## Hybrid Radiography

This is a repository for rapid generation of synthetic X-ray images.


## Installation

To install, use [Anaconda](https://www.anaconda.com/).

```bash
conda env create -n "hyrad" --file "hy_rad.yml"

conda activate hyrad
```

## Creating iPython kernel for jupyter

If using jupyter notebooks, you must remember to create the environment-specific ipython kernel

```bash
conda activate hyrad

python -m ipykernel install --user --name hyrad --display-name "Anaconda Hyrad"
```

To select in jupyter, search the "Kernel" dropbown menu -> "Change Kernel" -> "Anaconda Hyrad"

if you get the error message  "Module use of python36.dll conflicts with this version of Python.", this will (hopefully) be why.


## License

To be determined

## Contributing Authors

Robert Culver
