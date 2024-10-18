# binary.asm

        INP
        STA input

bitLoop	LDA one
        STA result
        LDA bCount
        BRZ powEnd
        SUB one
        STA power

powLoop	LDA powTwo
        SUB one
        STA pCount
        LDA result
        STA working
        LDA zero
        STA result

loop	LDA result
        ADD working
        STA result
        LDA pCount
        SUB one
        STA pCount
        BRP loop
        LDA power
        SUB one
        STA power
        BRP powLoop

powEnd	LDA result
        STA bitVal
        LDA bCount
        SUB one
        STA bCount
        ADD one
        BRP skip
        BRA end

skip	LDA input
        SUB bitVal
        BRP bitHigh
        LDA zero
        OUT
        BRA bitLoop

bitHigh	STA input
        LDA one
        OUT
        BRA bitLoop

end	HLT

input	DAT 0
one	DAT 1
zero	DAT 0
bitVal	DAT 0
bCount	DAT 7
powTwo	DAT 2
result	DAT 1
working	DAT 0
pCount	DAT 0
power	DAT 0
