# Final Fantasy VI Cid's Magitek Toolbox

## Table of contents

* [Disclaimer](#disclaimer)
* [Versions](#versions)
  * [v1.0.1](#v101)
  * [v1.0.0](#v100)
* [Requirements](#requirements)
* [Installation](#installation)
  * [Test your Python version](#test-your-python-version)
  * [Download](#download)
* [Scripting](#scripting)
  * [Artifacts](#artifacts)
    * [Memory Map](#memory-map)
    * [Flags](#flags)
    * [Variables](#variables)
      * [Constants](#constants)
        * [Using constants](#using-constants)
      * [Labels](#labels)
        * [Fixed labels](#fixed-labels)
        * [Relative labels](#relative-labels)
        * [Using labels](#using-labels)
    * [Comments](#comments)
  * [Data Structures](#data-structures)
    * [Instructions](#instructions)
      * [Flag setter instructions](#flag-setter-instructions)
      * [Moving block instructions](#moving-block-instructions)
    * [Pointers](#pointers)
      * [Direct pointers](#direct-pointers)
      * [Relative pointers](#relative-pointers)
    * [Blobs](#blobs)
    * [Strings](#strings)
    * [Arrays](#arrays)
* [Disassembly](#disassembly)
  * [Section modes](#section-modes)
    * [Instructions](#instructions-1)
    * [Pointers](#pointers-1)
      * [Relative pointers](#relative-pointers-1)
    * [Blobs](#blobs-1)
    * [Strings](#strings-1)
    * [Arrays](#arrays-1)
      * [Subsections](#subsections)
      * [Patterns](#patterns)
* [Assembly](#assembly)
* [Troubleshooting](#troubleshooting)
  * [Deactivating the logs](#deactivating-the-logs)
* [Special thanks](#special-thanks)

## Disclaimer

FF6CMT, or the Final Fantasy VI Cid's Magitek Toolbox, 
is a text-based editor allowing to modify assembly code and various types of
data in Final Fantasy 6.

Beware, the syntax used for some components may not be standard among other assemblers.

## Versions

### v1.0.2
* Fixed an issue where direct pointers were still considering the anchor if it was not None.

### v.1.0.1
* Fixed an issue where delimiters and anchors in the config file were not properly
taken into account during disassembly.
* Changed the way of detecting variable conflicts during parsing.
* Fixed an issue where a label added via an instruction would not write the address if
needed during script dumping.

### v1.0.0
* Initial version.

## Requirements

This tool requires:

* Python 3.11 or newer
* A Final Fantasy 3 US ROM

> [!IMPORTANT]
> A headered ROM *may* be used for disassembly, but a non-headered ROM **MUST**
> be used for assembly.

> [!NOTE]
> Any Super Nintendo ROM can be used here, but certain features are 
> specifically made for FF6.

## Installation

### Test your Python version

You may want to verify which version of Python you have installed. To do this,
open a terminal and enter the following command:

On Windows,
```
py --version
```

On Linux,
```
python3 --version
```

As long as the version is equal to or higher than `Python 3.11.0`, you're good
to go. If it is not, you may go on the 
[Python downloads page](https://www.python.org/downloads/) and follow the
instructions according to your OS.

### Download

In order to use FF6CMT, simply download the code from Github by clicking on 
the "Code" button in green and select "Download Zip", extract it to the folder
of your choice. Alternatively, you may just
[clone the repository](https://docs.github.com/en/repositories/creating-and-managing-repositories/cloning-a-repository).

## Scripting

Scripting refers to the creation or modification of assembly files. Unless otherwise
specified, every component is case-sensitive.

### Artifacts

Artifacts are tools used by FF6CWB to better understand how to properly assemble a script
into a ROM. However, they don't correspond to data in the ROM.

#### Memory Map

**Mandatory** in at least one of the script files used for assembling, the memory map allows
the application to determine the correspondence between the component's position in the
ROM and its address in the address space. To set the 
[mapping mode](https://snes.nesdev.org/wiki/Memory_map) of the memory map, you simply 
define it at the beginning of a script file like this:

``` 
map: HiROM
```

Accepted values are: 'LoROM', 'HiROM' and 'ExHiROM'.

> [!NOTE]
> All versions of Final Fantasy 6 are HiROM, although some romhacks, such as T-Edition,
> have been upgraded to ExHiROM.

#### Flags

Some instructions for the 65C816 takes an operand of either one or two bytes, depending
on the state of two specific flags: the 'm' flag that manages the width the accumulator,
or A register, and the 'x' flag that manages the width of the indexes, or X and Y
registers. When either flag is true, the corresponding register width is 8-bit. When it
is false, the register width becomes 16-bit.

To set the states of the flags directly in the script, you have to include:

```
m = 8, x = 16
```

Accepted values are '8' and '16'. Both flags have to be set at the same time.


> [!IMPORTANT]
> It is important to set the flags at any point in the script before the first
> instruction, even if that instruction sets the states of the flags.


#### Variables

Variables are basically named values. Although they are named variables, they can't be
modified once they are set.

The only characters accepted for variables names are lowercase letters, underscores and
numbers. The name must start with a letter. Also, variable names can't be the same as words
that are used to defined components, such as 'm', 'x', 'ptr', 'desc', etc.

> [!TIP]
> All variables are global, even when spread across multiple scripting files. An error will be
> thrown if a variable is defined twice. It might therefore be a good idea to put all
> commonly used variables and labels into their own file.

##### Constants

Constants are 8-bit and 16-bit variables. They are preferably defined at the beginning
of a script file, although they can be defined at any point before their first usage.
To define Constants, you can do:

```
let some_8_bit_constant = $12
let some_16_bit_constant = $3456
let delimiter = $FF
```

###### Using constants

To use a constant, simply replace the value of the operand by the name of the variable:

```
  LDA #$12 => LDA #some_8_bit_constant ; Notice that the dollar sign is always a part of the value)
  STA ($3456,X) => STA (some_16_bit_constant,X)
  "Some string",$FF => "Some string",delimiter
```

##### Labels

Labels are 24-bit variables that contain an address. They come in two flavours: fixed
and relative.

###### Fixed labels

Fixed labels contain their address of destination. It will also make the script consider
the label address as the current one and therefore allows to skip ahead to different
sections of the ROM that you want to modify.

```
@some_label = $C01234
```

In this case, regardless of the address of the previous data structure, the address of
the next one will be \$C01234.

> [!TIP]
> You can skip to a lower address, although it is not recommended as it can rapidly
> become a mess when the code is not in order.

###### Relative labels

As their name might suggest, relative labels do not contain a fixed address. They will
obtain whatever address the script is currently at when parsing the label line. This
allows to code sections of code without having to constantly recalculate the label
address. To create a relative label, simply do not insert any address:

```
@some_label = $C01234
  LDA #$5678

@some_other_label ; Will obtain the address $C01237 
```

###### Using labels

To use the full 24-bit address, simply replace the operand value with the name of the label.

```
  LDA $C01234 => LDA some_label
```

It is also possible to use labels as 8 or 16-bit addresses. Using a label as a 8-bit variable
will return the bank of the address. To do so, use the prefix '.' in front of the variable.
For example:

```
  LDA #.some_label ; Corresponds to LDA #$C0
```

Using it a 16-bit will return the 2 least significant bytes or the address, or the relative
address. To do so, use the prefix '!'.

```
  ptr $1234 => ptr !some_label ; Assuming the pointer is in bank C0.
  JMP ($1234,X) => JMP (!some_label,X)
```

> [!IMPORTANT]
> Labels in branching instructions, such as 'BRA' or 'BCS', do not require a prefix as their
> values are calculated in a different way.
> ```
>   BRA some_other_label
> ```

#### Comments

You can leave comments to facilitate reading by putting a semicolon as the end of a line.

```
; This is a comment that takes a whole line.
  LDA #$12 ; This is a comment added at the end of a line.
```

### Data Structures

Data structures refer to structures that actually can be disassembled from or assembled
into a ROM.

#### Instructions

When talking about disassembling, we are generally talking about disassembling the
instructions for the processor. Here, the processor is the 65C816 and information about
its set of instructions can be found
[here](https://6502.org/tutorials/65c816opcodes.html).

An instruction is composed of two parts: the command and the operand. The command is
composed of 3 capital letters.

> [!NOTE]
> The only difference between the instructions as explained in the link above and in 
> FF6CMT is the usage of 'JML' instead of 'JMP' when the operand is 24-bit, similarly
> to 'JSR' and 'JSL'. The reason came as a necessity during development in order to be 
> able to "guess" the length of the instruction to properly assess the labels' addresses
> further down the script.
 
The second part of the instruction is called the operand. Operands can be between 1 and 3
bytes and are not always required, depending on the instruction.

```
  BRK
  LDA #$12
  ADC ($1234),X
  STA $301234
```

The operand can be set with a value, as shown above, or a variable. In the case of variables,
please refer to the [Variables](#variables) section on how to use them.

##### Flag setter instructions

The instructions "[REP](https://6502.org/tutorials/65c816opcodes.html#6.4.2)" and "SEP" are 
important to set the width of the 'm' and the 'x' flags. FF6CMT will update its own flags' states
when parsing such a line. '#\$10' correspond to the 'x' flag and '#\$20' correspond to the 'm'
flag.

```
  REP #$20 ; After parsing this instruction, the 'm' flag will become false, or 16-bit.
  SEP #$30 ; After parsing this instruction, both the 'm' and 'x' flag will become true, or 8-bit.  
```

> [!IMPORTANT]
> There lies in the 65C816 processor the 'e', or emulation, flag. This application assumes that
> that flag is never set as it forces the 'm' and 'x' flags to be true (there are other effects,
> but I haven't dwelt much into that part of the documentation.)

##### Moving block instructions

The instructions "MVN" and "MVP" have effectively two operands and either one, or both, of them 
can be replaced with a variable.

```
  let some_8_bit_constant = $12
  let yet_another_variable = $34

  MVN #$12,#$34
  MVP #some_8_bit_constant,#yet_another_variable
```


#### Pointers

Pointers are 16-bit, or relative, addresses used to jump around in the code or read something
off a table. They either can be direct or relative pointers.

> [!NOTE]
> 'Direct' and 'relative' do not refer here to the addressing mode of the instructions with the
> same names, but just if the value can be derived directly to obtain the address of the 
> destination or relatively from a specific anchor.

##### Direct pointers

They can be used when the pointer and the destination are in the same bank.

```
@somewhere_in_the_d2_bank = $D23333
  ptr $89AB ; The destination will be $D289AB.
```

##### Relative Pointers

They can be used from anywhere and point to any address in the address space. They however
require an "anchor", i.e. the address considered the start of the table.

```
#some_label ; $C01234
  rptr $000A
  
#$C03333
  rptr !some_other_label ; Let's assume that some_other_label is at $C04444.
```

As you can see, you can use either an address or a label as the anchor (they do not take 
constants). In the first case, anchor is \$C01234, so the pointer destination will be \$C0123E.

In the second case, the anchor is \$C03333 and the destination is \$C04444, so the value of
the pointer will be \$1111.

> [!WARNING]
> Be careful when moving around a table which is pointed at by relative pointers as the
> address of the anchor is most likely hardcoded somewhere in the code. If you know where
> that address is set, I suggest you disassemble that part of the code and make it more
> flexible by changing the bank and relative address of the anchor with the 8 and 16-bit
> representation of the label. See the section on [labels](#labels) above for more detail.

#### Blobs

Blobs are simple the simplest representation of bytes that can be written in the script. 
What you see is what you get, unless you're using variables. They either have a specific length
or a delimiter. A delimiter is a one-byte character that tells the game that the blob is over.

> [!TIP]
> Blobs are displayed in little endian, regardless of their length. Therefore, it is
> recommended to keep the length of each blob low, even though the application doesn't
> provide any limit.

```
  $12 ; Simply the byte \x12
  some_8_bit_constant ; Also the byte \x12
  
  $1234,$FF ; Simple the bytes 0x34 and 0x12 (the bytes are written in little endian).
            ; with the delimiter 0xFF.
  some_16_bit_constant,delimiter ; The same thing as above, but with variables. 
```

#### Strings

Strings are series of bytes destined to be read in some form during the game. There are
currently two types of strings being supported, menu strings (such as 'LV', 'HP', 'Items') and
menu descriptions, used for the spells, items, etc.

Like blobs, they come with either a specific length or a delimiter.

The type of string is determined by its prefix. No prefix refers to a menu string and 'desc'
refers to a menu description.

```
  "Blitz   " ; A menu string with a fixed length of 8 which had to be padded with spaces.
  desc "Some description with a delimiter",$FF 
```

> [!NOTE]
> In the future, the goal would be to be able to set any type of strings with a custom charset.

#### Arrays

Arrays are used for tables and comprised of blobs and strings. Each cell is independent of 
the others, so they can each have a defined length or a delimiter.

```
  $12 | "Some string" | some_8_bit_constant,$00 | desc "Some other string",delimiter ; some comment
```

> [!NOTE]
> It is unlikely to encounter such an array in the wild. Most tables are strictly composed of
> blobs or are composed of a set of coordinates with a string.

## Disassembly

Disassembly is the process of interpreting the binary code of a ROM and 
transforming it into human-readable code.

In order to do so with FF6CMT, you must first create a file called `config.toml`
at the root of the project with a section called `disassembly` like this.

```
[disassembly]
source = "source.smc"
destination = "destination.asm"
mapping_mode = "HiROM"
sections = [
  {start = 0x03001B, end = 0x030057, mode = "INSTRUCTIONS", flags = {"m" = 8, "x" = 16} },
  {start = 0x2D8634, end = 0x2D8BCA, mode = "ARRAYS", pattern="treasure_chests"},
]
```

* `source`: The source ROM that will be used for disassembly. It is
recommended to use a non-headered ROM. You *may* use a headered ROM, but you
will have to account for the 512 bytes of displacement of code in the section
positions.
* `destination`: The destination assembly file.
* `mapping_mode`: The mapping mode of the
[memory map](https://snes.nesdev.org/wiki/Memory_map). Can be `LoROM`, `HiROM`
or `ExHiROM`. FF6 is a HiROM, but some hacks, such as T-Edition, converted the ROM
to ExHiROM.
* `sections`: The different parts of the ROM that you want to disassemble.
  * `start`: The first byte of the section.
  * `end`: The first byte after the end of the section.
  * `mode`: Section modes will be explained in the following section.
  * __Other parameters:__ They are used for specific section modes and will be
explained in the following section as well.

> [!IMPORTANT]
> "start" and "end" values must be ROM position, ranging from 0 to 0x3FFFFF for HiROMs,
> and NOT the address in the memory space, which ranges from 0xC00000 to 0xFFFFFF for
> HiROMs.

Once you created or modified the file, open a terminal, go to the project directory and
enter the following command:

On Windows
```
py disassemble.py
```

On Linux
```
python3 disassemble.py
```

### Section Modes

The section mode helps FF6CMT how it should disassemble the data.

#### Instructions

Instructions are a set of commands interpreted by the processor. In the case of 
the 65C816 processor, the operand of some instructions may have a different width
(or number of bytes) depending on the values of two flags, the 'm' flag for the 
accumulator (or A register) and the 'x' flag for the X and Y indexes. Therefore, 
they need to be set when defining the section like this:
```
{start = 0x03001B, end = 0x030057, mode = "INSTRUCTIONS", flags = {"m" = 8, "x" = 16} }
```

> [!NOTE]
> Any branching or jumping instruction, as well as instructions with a 24-bit operand,
> found while disassembling will automatically create a label of the destination and
> change the operand to the label's name.

#### Pointers

Pointers are 16-bit values that refer to the address of an entry in a list. By
default, the value references the address within the bank itself.

For example, a pointer with a value of \$1234 in the bank C0 will point to the 
address \$C01234. Setting a pointers section can be done like this:

```
{start = 0x0301DB, end = 0x0302DB, mode = "POINTERS"}
```

> [!NOTE]
> Every pointer will generate a label of the destination and change the operand to 
> the label's name.

##### Relative Pointers

Sometimes, though, the pointer's value is not in reference to the beginning of a bank,
but the beginning of a section itself, often in a different bank. In which case, you
need to define the "anchor", or the address from which the pointer's value will be
derived.

For example, a pointer with an anchor at \$D34500 and a value of \$1234 will point to the
address \$D35734, regardless of the bank in which the pointer stands. To define a section
of relative pointers, it needs to be done this:

```
{start = 0x0301DB, end = 0x0302DB, mode = "POINTERS", anchor=0x123456}
```

> [!IMPORTANT]
> Like for "start" and "end", the "anchor" value is the ROM position, not the address
> in the memory space.

#### Blobs

Blobs are a simple way to directly portray bytes without any interpretation. They can
be either of a fixed length or have a delimiter, i.e. a specific byte that we are
looking for to end the blob. You may use one or the other, like this:

```
{start = 0x001100, end = 0x0012FF, mode = "BLOBS", length=2}
```

or

```
{start = 0x001100, end = 0x0012FF, mode = "BLOBS", delimiter=0xFF}
```

#### Strings

As their name indicates, strings are series of bytes used to be read during the game.
They function much like blobs, i.e. they can be set with either a length or a delimiter,
with the added requirement of defining a type of string. To define a strings section, you
can do:

```
{start = 0x001100, end = 0x0012FF, mode = "STRINGS", length=8}
```

or

```
{start = 0x001100, end = 0x0012FF, mode = "STRINGS", delimiter=0xFF}
```

#### Arrays

Arrays are rows in tables that mix blobs and strings. Such tables can be list of
coordinates followed by a string or the treasures chests table, for example. To properly 
define an arrays section, you either have to define the subsections or a pattern.

##### Subsections

Think of the subsections as individuals cells in the row. Each row can contain either
a string or a blob, defined by either their length or a delimiter. An array defined as
containing all 4 combinations can look like:

```
{start = 0x001100, end = 0x0012FF, mode = "ARRAYS", subsections=[
  {mode = "BLOBS", length = 2},
  {mode = "BLOBS", delimiter = 0x00},
  {mode = "STRINGS", length = 13},
  {mode = "STRINGS", delimiter = 0xFF},  
]}
```

##### Patterns

Patterns are hard-coded types of arrays that adds related variables to facilitate
modifying them.

> [!NOTE]
> Currently, there is only "treasure_chests" available. But alongside setting the five 
> subsections, it will also add the treasure type values and item names as variables.
> It will take the variable names and values in the file 'variables.json'
> It won't replace the enemy formations by a variable, for the moment. at the root of the
> project. In a future update, that file will be customizable. Here, it was more a proof of
> concept.

For example, in unheadered vanilla, defining the arrays section looks like:

```
{start = 0x2D8634, end = 0x2D8BCA, mode = "ARRAYS", pattern="treasure_chests"}
```

## Assembly

Once your script is ready to be tested, create a section called `[assembly]` in the file
`config.toml` like this:

```
[assembly]
source = "ff3.smc"
destination = "test.smc"
scripts = [
    "examples/devastating_critical.asm",
    "examples/new_status_page.asm",
]
```

* `source`: The source ROM.
* `destination`: The destination ROM. It will be a copy of the source ROM with the assembled
script on top of it.
* `scripts`: A list of all script files that will be assembled in the destination ROM.

Once you created or modified the section, open a terminal, go to the project folder and enter
the following command:

On Windows
```
py assemble.py
```

On Linux
```
python3 assemble.py
```

## Troubleshooting

In order to facilitate troubleshooting, logging is available. Whenever the assemble.py or
disassemble.py are executed, FF6CMT checks for the existence of the file `logging.conf` at
the root of the project and copied it from `template_logging.conf` is it doesn't exist. By
default, it will grant access to logs in two forms:

* Directly in the console.
* In a log file.

The latter contains more information as it also contains the debug-level logs. You may change
that by modifying `logging.conf`. More information about this 
[here](https://docs.python.org/3/library/logging.config.html#configuration-file-format).

Hopefully, the error messages and the logging will provide enough information to help you
figure out what is the issue.

### Deactivating the logs

In order to prevent logging, either in the console or on file, simply modify `logging.conf`
and modify line 6. You can remove either the mention of `file` or `console` or both, but
you have to keep `handlers=` at the very minimum.

> [!TIP]
> Deleting `logging.conf` won't work as it will simply be recreated next time you execute
> `assemble.py` or `disassemble.py`.

## Bug report

If you think you stumbled upon a bug, do not hesitate to reach out in one of the following
ways:

* Submit a bug report on Github.
* Email me at thenpcnextdoor@pm.me.

Alternatively, you can reach out in the ff6hacking discord server, but I'll probably
eventually ask you to formalize the bug report. When doing so, please provide the related logs,
the script you're attempting to assembling, if applicable, and whether you're using the
original ROM or some hacked version.

## Special thanks

I would like to thank my family and friends, especially Fred and Mathieu, whom I pestered
relentlessly with unprompted updates on this project over the years! I would also like to
thank the ff6hacking.com community for keeping the FF6 hacking scene alive all these years. 