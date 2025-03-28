package main

import (
	"fmt"
	"os"
)

var InstructionSetA = map[byte]string{
	0x11: "LDR",
	0x12: "LDRI",
	0x15: "STR",
	0x16: "STRI",
	0x2A: "MOV",
	0x41: "ADD",
	0x42: "SUB",
	0x47: "MUL",
	0x71: "LSL",
	0x73: "LSR",
	0x7A: "XOR",
	0x7B: "AND",
	0xFE: "RET",
	0xFF: "HLT",
}

var InstructionSetB = map[byte]string{
	0x13: "LDR",
	0x14: "LDRI",
	0x17: "STR",
	0x18: "STRI",
	0x2B: "MOV",
	0x91: "ADD",
	0x92: "SUB",
	0x97: "MUL",
	0xC1: "LSL",
	0xC3: "LSR",
	0xCA: "XOR",
	0xCB: "AND",
	0xFE: "RET",
	0xFF: "HLT",
}

func dis(instrSet map[byte]string, bytecode [4]byte) {

	opcode := bytecode[0]
	operands := bytecode[1:]

	if instr, exists := instrSet[opcode]; exists {
		switch instr {
		case "LDR":
			fallthrough
		case "STR":
			fmt.Printf("%s R%d, R%d", instr, operands[0], operands[1])
		case "LDRI":
			fallthrough
		case "STRI":
			fmt.Printf("%s R%d, #%x", instr, operands[0], operands[2])
		case "MOV":
			imm := int32(operands[1]) + int32(operands[2])<<8
			fmt.Printf("%s R%d, #%x", instr, operands[0], imm)
		case "RET":
			fmt.Printf("%s R%d", instr, operands[0])
		case "HLT":
			fmt.Printf("%s", instr)
		default:
			fmt.Printf("%s R%d, R%d, R%d", instr, operands[0], operands[1], operands[2])
		}
		fmt.Print("\n")
	}
}

func disasm(instrSet map[byte]string) {
	var instrcode [4]byte
	data, _ := os.ReadFile("bytecode_dump.bin")
	for i := 0; i < len(data); i += 4 {
		copy(instrcode[:], data[i:i+4])
		dis(instrSet, instrcode)
	}
}

func main() {
	disasm(InstructionSetA)
	disasm(InstructionSetB)
}
