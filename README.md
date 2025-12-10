MiniLang LL(1) Parser – README

This project implements a simple lexer and LL(1) recursive-descent parser for a small educational language called MiniLang.

The purpose of the project is to practice the core steps of compiler design:
- Lexical analysis (tokenization)
- Grammar design for an LL(1) language
- FIRST and FOLLOW sets (in the report)
- LL(1) parse table (in the report)
- LL(1) parser implementation
- Printing "Program başarıyla parse edildi." and leftmost derivation steps for valid programs
- Printing syntax error messages for invalid programs

1. Requirements
- Python 3.x
- No external libraries required

2. Files
- mini_ll1.py  
  Main source file containing:
  - Token definition
  - Lexer implementation
  - Recursive-descent LL(1) parser
  - Leftmost derivation recording
  - main() function to run the parser

- ornek.mini  
  Valid MiniLang sample program (used for successful example output)

- invalid_test.mini  
  Invalid MiniLang sample program (used for syntax error example output)

3. MiniLang Language (Short Description)
- Single data type: int
- Variable declarations:
    int x;
    int y;

- Assignment statements:
    x = 3 + 4 * 2;
    y = (x - 5) / 2;

- Arithmetic operators: +, -, *, /
- Parenthesized expressions
- Print statement:
    print(x);

- Single-line comments:
    // this is a comment

The full grammar, FIRST/FOLLOW sets and LL(1) parse table are included in the PDF project report.

4. How to Run
1. Open a terminal in the folder containing mini_ll1.py.
2. To run the parser on a valid MiniLang program:
       python mini_ll1.py ornek.mini

   Output will include:
   - Token stream
   - "Program başarıyla parse edildi."
   - Leftmost derivation steps
3. To run the parser on an invalid MiniLang program:
       python mini_ll1.py invalid_test.mini

   Output will include:
   - Token stream
   - Syntax error message such as:
       Syntax error at line 2, near token ID (value 'x') - expected SEMICOLON

5. Error Handling
- Lexical errors:
  Illegal characters result in a LexerError with line and column information.

- Syntax errors:
  ParserError is raised when a production cannot be matched.  
  The message contains:
    - line number
    - token/value
    - expected token(s)

If any error occurs, no success message or derivation steps are printed.
