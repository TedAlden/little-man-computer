# countdown.asm

        INP
        STA x

loop    LDA x
        OUT
        SUB one
        STA x
        BRZ end
        BRA loop

end     LDA x
        SUB x
        OUT
        HLT

x       DAT
one     DAT 1
