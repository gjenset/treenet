# treenet

## What is TreeNet?

TreeNet is a Python module for extracting potential constructions from Penn-Helsinki style parsed historical corpora (https://www.ling.upenn.edu/hist-corpora/). The term "constructions" is meant in fairly broad sense, but one that is compatible with usage based approaches to Construction Grammar (CxG). The aim of TreeNet is to help identify potential types of constructions and instances of constructions, without being tied to a particular theoretical flavour of CxG.

## What does TreeNet do?

TreeNet finds freqent combinations of corpus tags from the corpus files, cleans them, and outputs them to files for further analysis. TreeNet is inspired by, but different from, other construction identification applications such as StringNet (https://aclanthology.org/W10-0804.pdf). In particular, TreeNet (as the name implies) relies on the syntactic annotation of the corpus files. This is partly due to the grammatical and spelling variation found in earlier language varieties, which makes it hard to implement a truly lexical bottom-up approach, without first normalising spelling. But using the parsed corpus annotation also means that TreeNet can more easily identify relevant constructions at the main clause level.

## What is required to use TreeNet?

To use TreeNet you must download the Python file with the module, have Python installed, and have access to Penn-Helsinki style parsed historical corpus files on your system (.psd) files.

## How is TreeNet used?

TreeNet can be used in two modes, either as a script or as a Python module inside another script. To use it as a script, open a command line window in the TreeNet folder and type:

```python treenet.py "<data_path>" "<output_path>"``` 

where the two arguments are strings with the path to the .psd files on your computer and the location where you want the output files, respectively.

To use TreeNet as a module, make sure that the treenet.py file is in a location where the Python interpreter can find it. It can then be called like this:

```
import treenet as tnt

my_input_files = "foo\bar\data"
my_output_files = "foo\bar\out"
tnt.get_constructions(my_input_files, my_output_files, min_freq=5, sep="\t")
```

There are additional parameters to set the minimum frequency of constructions and the separator value for output files. The default values are illustrated above.

## How to cite TreeNet and where to find more details?

I plan to publish an open access code metapaper which will serve as an elaboration of the software, the use cases, and limitations, as well as serving as a standard academic reference.

