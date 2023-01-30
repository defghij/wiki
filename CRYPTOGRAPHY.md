# Contents

- [Introduction](#introduction)
- [Hashes](#hashes)
  - [SHA](#sha)
  - [MD5](#md5)
- [Ciphers](#ciphers)
  - [Modes](#modes)
  - [AES](#aes)

# Introduction

Wikipedia defines [Cryptography](https://en.wikipedia.org/wiki/Cryptography) as the practice and study of securing communications and data from adversarial inspection. There is also the field of [Cryptanalysis](https://en.wikipedia.org/wiki/Cryptanalysis) which can be thought of as the attack side to cryptography's defensive side. Much like penetration testing for networks and computer system, any good crypto-system will have been subjected to rigorous cryptanalysis. For the purpose of this wiki I'll note distiguish between the two.

There are two broad classes of cryptograhic algorithms: Hashes and Ciphers. A hash is the result of some function that takes input and output a fixed size, hopefully, pragmatically unique series of bits. Hashes can be used as signatures or validation of data. Ciphers are a class of functions that take an input stream and output a byte stream that obsfucates or hides the original input stream. A cipher usually has an encryption function which takes plaintext, the data we want to encrypt, and transforms it into ciphertext, a seemingly randion collection of bits. The decryption function reverses this process taking ciphertext as input and outputing plaintext.

# Hashes

## Key derivation

## Message Authentication Code

## Hash Algorithms

### SHA

### MD5

# Ciphers

## Modes

### Streaming

### Block
