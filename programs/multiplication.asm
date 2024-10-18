# multiplication.asm

        INP
        STA a
        INP
        STA b

loop    LDA b
        BRZ end
        SUB ONE
        STA b
        LDA ans
        ADD a
        STA ANS
        BRA loop

end     LDA ans
        OUT
        SUB ans
        STA ans
        HLT

a       DAT
b       DAT
ONE     DAT 1
ans     DAT 0
