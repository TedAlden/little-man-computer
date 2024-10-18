# exponentiation.asm

          LDA one
          STA result
          INP
          STA base
          INP
          STA exponent

outerloop LDA exponent
          BRZ end
          SUB one
          STA exponent
          LDA zero
          STA product
          LDA base

innerloop BRZ exloop
          SUB one
          STA countdown
          LDA product
          ADD result
          STA product
          LDA countdown
          BRA innerloop

exloop    LDA product
          STA result
          BRA outerloop

end       LDA result
          OUT
          HLT

# variables

base      DAT
exponent  DAT
countdown DAT
result    DAT
product   DAT

# constants

one       DAT 1
zero      DAT 0
