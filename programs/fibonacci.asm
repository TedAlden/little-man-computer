# fibonacci.asm

        INP
        SUB one
        STA count

start   LDA a
        ADD b
        STA next
        OUT
        LDA b
        STA a
        LDA next
        STA b
        LDA count
        SUB one
        STA count
        BRP start
        HLT

a       DAT -1
b       DAT 1
next    DAT 0
count   DAT 0
one     DAT 1
