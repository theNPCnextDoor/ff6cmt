map: HiROM
let alfa = $12
let bravo = $1234
let delta = $00
let item_dummy = $01
let treasure_miab = $20
let treasure_item = $40

@archie = $C00005
m = 8, x = 16
  TAX ; some comment
  LDA (alfa,X)
  LDX #$FEDC
  REP #$30
  LDA #bravo
  LDX #$FEDC
  SEP #$30
  LDA #.label_c0fedc
  LDX #$CC
  MVP #$34,#alfa

  JMP !archie
  BRA start ; some other comment

  bravo
  $5678,$FF
  $ABCD,delta
  "<0x00>A<KNIFE>_",$88
  $AA | "a" | $BB,$FF | "b",$00

  desc "Bob
<FIRE>",$00

#anchor_1
  rptr !rptr_1
  rptr !rptr_2

#$D20002
  rptr !rptr_2
m = 8, x = 8 ; Unnecessary flags redefinition here.
  JSR !archie
  $12 | $34 | $56 | treasure_item | item_dummy
  $78 | $AB | $CD | treasure_miab | $01

  dlg "Th
<PAGE>
<0x17: 34><SPACES: 08>",$00

@label_c0fedc = $C0FEDC
@anchor_1 = $D20001
@rptr_1 = $D23456
@rptr_2 = $D23457
m = 16, x = 16
  JSL archie