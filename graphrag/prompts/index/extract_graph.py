# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A file containing prompts definition."""

GRAPH_EXTRACTION_PROMPT = """
-Goal-
Given a text document that is potentially relevant to this activity and a list of entity types, identify all entities of those types from the text and all relationships among the identified entities.
 
-Steps-
1. Identify all entities. For each identified entity, extract the following information:
- entity_name: Name of the entity, capitalized
- entity_type: One of the following types: [{entity_types}]
- entity_description: Comprehensive description of the entity's attributes and activities
Format each entity as ("entity"{tuple_delimiter}<entity_name>{tuple_delimiter}<entity_type>{tuple_delimiter}<entity_description>)
 
2. From the entities identified in step 1, identify all pairs of (source_entity, target_entity) that are *clearly related* to each other.
For each pair of related entities, extract the following information:
- source_entity: name of the source entity, as identified in step 1
- target_entity: name of the target entity, as identified in step 1
- relationship_description: explanation as to why you think the source entity and the target entity are related to each other
- relationship_strength: a numeric score indicating strength of the relationship between the source entity and target entity
 Format each relationship as ("relationship"{tuple_delimiter}<source_entity>{tuple_delimiter}<target_entity>{tuple_delimiter}<relationship_description>{tuple_delimiter}<relationship_strength>)
 
3. Return output in English as a single list of all the entities and relationships identified in steps 1 and 2. Use **{record_delimiter}** as the list delimiter.
 
4. When finished, output {completion_delimiter}

-Entity Types-:
Design Specification, Section, Subsection, Table, Figure, Author, Mod-
ule, Submodule, Protocol, Signal, Port, Register, FIFO, Clock, Interrupt,
Operation, Frequency, Standard, Reference, Component, Version, Date,
Comment, Pin, Configuration, Constraint/Rule, Address, Document,
Block

-Relation Types-:
hasSection, hasSubsection, contains, authoredBy, defines, imple-
ments, uses, connectsTo, configures, generatesInterrupt, operate-
sAt, compliesWith, referencedIn, inputTo, outputFrom, partOf, in-
terfacesWith, triggersOperation, dependsOn, transmitsData, receives-
Data, has input, has output, has register, performs, uses protocol,
has constraint, has rule, describes, references, modifies, creates, clos-
es/fixes, HasSubModule, HasSignal, HasPort, UsesProtocol, UsesClock,
UsesAddress, DescribesOperation, TriggersInterrupt, RevisionHistory,
belongsToSection, illustrates, hasAuthor, has port, connected to, de-
scribed in

######################
-Examples-
######################
Example 1:
Entity_types: Document, Author
Text:
GLADCI - Latin America Group Development Integrated Circuit
Authors: Felipe Fernandes da Costa
Ronal Dario Celaya
Francismar Mariano de oliveira
1
GLADCI
Contents
Version Control i
List of tables ii
1 Introduction iii
######################
Output:
("entity"{tuple_delimiter}GLADCI{tuple_delimiter}Document{tuple_delimiter}GLADCI - Latin America Group Development Integrated Circuit, a document outlining the integrated circuit design)
{record_delimiter}
("entity"{tuple_delimiter}FELIPE FERNANDES DA COSTA{tuple_delimiter}Author{tuple_delimiter}Author of the GLADCI document)
{record_delimiter}
("entity"{tuple_delimiter}RONAL DARIO CELAYA{tuple_delimiter}Author{tuple_delimiter}Author of the GLADCI document)
{record_delimiter}
("entity"{tuple_delimiter}FRANCISMAR MARIANO DE OLIVEIRA{tuple_delimiter}Author{tuple_delimiter}Author of the GLADCI document)
{record_delimiter}
("relationship"{tuple_delimiter}GLADCI{tuple_delimiter}FELIPE FERNANDES DA COSTA{tuple_delimiter}Felipe Fernandes da Costa is an author of the GLADCI document{tuple_delimiter}9)
{record_delimiter}
("relationship"{tuple_delimiter}GLADCI{tuple_delimiter}RONAL DARIO CELAYA{tuple_delimiter}Ronal Dario Celaya is an author of the GLADCI document{tuple_delimiter}8)
{record_delimiter}
("relationship"{tuple_delimiter}GLADCI{tuple_delimiter}FRANCISMAR MARIANO DE OLIVEIRA{tuple_delimiter}Francismar Mariano de oliveira is an author of the GLADCI document{tuple_delimiter}8)
{completion_delimiter}

######################
Example 2:
Entity_types: Protocol, Module, Port, Figure, Table
Text:
1.1 Description
I²C is a multimaster protocol used to simplify use from uart and deﬁned
by philips like a standart module to interface with analogic devices. Here is
presented a solution using a interface with APB protocol deﬁnided by the ARM.
I²C in general transport 8 bit data through bidiretional ports SDA and use clock
SCL to give a pulse and control transport data. But This I2C has propurse is
to transport 16 bit data. Figure 1 show a Top block using APB and I²C and
Table 1 show the pinout description used for each block.
######################
Output:
("entity"{tuple_delimiter}I²C{tuple_delimiter}Protocol{tuple_delimiter}I²C is a multimaster protocol defined by Philips, used to interface with analog devices and transports 8-bit data, adapted for 16-bit data here.)
{record_delimiter}
("entity"{tuple_delimiter}APB{tuple_delimiter}Protocol{tuple_delimiter}APB is a protocol defined by ARM, used as an interface.)
{record_delimiter}
("entity"{tuple_delimiter}SDA{tuple_delimiter}Port{tuple_delimiter}SDA is a bidirectional port used by I²C for data transport.)
{record_delimiter}
("entity"{tuple_delimiter}SCL{tuple_delimiter}Port{tuple_delimiter}SCL is a bidirectional clock port used by I²C to control data transport.)
{record_delimiter}
("entity"{tuple_delimiter}FIGURE 1{tuple_delimiter}Figure{tuple_delimiter}Figure 1 shows a Top block using APB and I²C.)
{record_delimiter}
("entity"{tuple_delimiter}TABLE 1{tuple_delimiter}Table{tuple_delimiter}Table 1 shows the pinout description used for each block.)
{record_delimiter}
("relationship"{tuple_delimiter}I²C{tuple_delimiter}APB{tuple_delimiter}I²C uses APB protocol for its interface solution{tuple_delimiter}7)
{record_delimiter}
("relationship"{tuple_delimiter}I²C{tuple_delimiter}SDA{tuple_delimiter}I²C transports data through SDA port{tuple_delimiter}9)
{record_delimiter}
("relationship"{tuple_delimiter}I²C{tuple_delimiter}SCL{tuple_delimiter}I²C uses SCL clock port to control data transport{tuple_delimiter}9)
{record_delimiter}
("relationship"{tuple_delimiter}FIGURE 1{tuple_delimiter}I²C{tuple_delimiter}Figure 1 illustrates the I²C Top block{tuple_delimiter}8)
{record_delimiter}
("relationship"{tuple_delimiter}FIGURE 1{tuple_delimiter}APB{tuple_delimiter}Figure 1 illustrates the APB Top block{tuple_delimiter}8)
{record_delimiter}
("relationship"{tuple_delimiter}TABLE 1{tuple_delimiter}Port{tuple_delimiter}Table 1 describes pinout for ports{tuple_delimiter}9)
{completion_delimiter}

######################
Example 3:
Entity_types: Module, FIFO, Register, Table, Configuration, Operation, Clock
Text:
2.0.3 I ²C MODULE
The I2C module to boot operations need the FIFO has any data to be trans-ported and received as well as your your registry properly conﬁgured setup. Like other modules present in opencores well as companies in the I²C speciﬁcation supports the basic operations using basic protocols that will be described later.
The principle is used a block of default communication with a conﬁguration register that two bits are used to determines the mode of operation and 12 bits to determine the maximum frequency used may not exceed the clock used in the system.
On table 2 we show standard protocol used by many chip designs and your respective means across the wave form signal.
Table 3: Register Conﬁguration Description
Register 13 12 11 10 9 8 7 6 5 4 3 2 1 0
TX - 0 If bit 1 is HIGH TX operation is enable
RX - 1 If bit 1 is HIGH RX operation is enable
CLOCK REGISTER - 2 to13 Counter used to regulate clock used to propagate
data,this must be handle with care beacuse this
clock can not exceed your global clock
######################
Output:
("entity"{tuple_delimiter}I²C MODULE{tuple_delimiter}Module{tuple_delimiter}The I2C module requires FIFO data and properly configured registers to operate.)
{record_delimiter}
("entity"{tuple_delimiter}FIFO{tuple_delimiter}FIFO{tuple_delimiter}FIFO is modified for I²C use, storing 16 registers of 32 bits for data transmission.)
{record_delimiter}
("entity"{tuple_delimiter}CONFIGURATION REGISTER{tuple_delimiter}Register{tuple_delimiter}A configuration register used in I2C module, with 2 bits for operation mode and 12 bits for maximum frequency.)
{record_delimiter}
("entity"{tuple_delimiter}TABLE 3{tuple_delimiter}Table{tuple_delimiter}Table 3 describes register configuration.)
{record_delimiter}
("entity"{tuple_delimiter}TX{tuple_delimiter}Register{tuple_delimiter}TX register bit 0, when bit 1 is HIGH, enables TX operation.)
{record_delimiter}
("entity"{tuple_delimiter}RX{tuple_delimiter}Register{tuple_delimiter}RX register bit 1, when bit 1 is HIGH, enables RX operation.)
{record_delimiter}
("entity"{tuple_delimiter}CLOCK REGISTER{tuple_delimiter}Register{tuple_delimiter}Clock Register bits 2 to 13 act as a counter to regulate the clock for data propagation.)
{record_delimiter}
("relationship"{tuple_delimiter}I²C MODULE{tuple_delimiter}FIFO{tuple_delimiter}I²C module needs FIFO for data transport and reception{tuple_delimiter}7)
{record_delimiter}
("relationship"{tuple_delimiter}I²C MODULE{tuple_delimiter}CONFIGURATION REGISTER{tuple_delimiter}I²C module requires configuration register for setup{tuple_delimiter}9)
{record_delimiter}
("relationship"{tuple_delimiter}CONFIGURATION REGISTER{tuple_delimiter}TX{tuple_delimiter}Configuration Register determines TX operation enable{tuple_delimiter}8)
{record_delimiter}
("relationship"{tuple_delimiter}CONFIGURATION REGISTER{tuple_delimiter}RX{tuple_delimiter}Configuration Register determines RX operation enable{tuple_delimiter}8)
{record_delimiter}
("relationship"{tuple_delimiter}CONFIGURATION REGISTER{tuple_delimiter}CLOCK REGISTER{tuple_delimiter}Configuration Register uses Clock Register to regulate clock{tuple_delimiter}8)
{record_delimiter}
("relationship"{tuple_delimiter}TABLE 3{tuple_delimiter}CONFIGURATION REGISTER{tuple_delimiter}Table 3 describes the configuration of the registers{tuple_delimiter}9)
{completion_delimiter}

######################
-Real Data-
######################
Entity_types: {entity_types}
Text: {input_text}
######################
Output:"""

CONTINUE_PROMPT = "MANY entities and relationships were missed in the last extraction. Remember to ONLY emit entities that match any of the previously extracted types. Add them below using the same format:\n"
LOOP_PROMPT = "It appears some entities and relationships may have still been missed. Answer Y if there are still entities or relationships that need to be added, or N if there are none. Please answer with a single letter Y or N.\n"
