import sys
import re
from dataclasses import dataclass
from typing import List, Optional

# TOKEN TANIMLARI

@dataclass
class Token:
    type: str   # Örn: 'INT', 'ID', 'NUMBER', 'PLUS', 'EOF'
    value: str  # Asıl metin: 'int', 'x', '3', '+'
    line: int
    column: int

    def __repr__(self):
        return f"Token({self.type}, {self.value!r}, {self.line}:{self.column})"


KEYWORDS = {
    "int": "INT",
    "print": "PRINT",
}

SINGLE_CHAR_TOKENS = {
    ';': "SEMICOLON",
    '=': "ASSIGN",
    '+': "PLUS",
    '-': "MINUS",
    '*': "MULT",
    '/': "DIV",
    '(': "LPAREN",
    ')': "RPAREN",
}


class LexerError(Exception):
    pass


class ParserError(Exception):
    pass


# LEXER

class Lexer:
    def __init__(self, text: str):
        self.text = text
        self.pos = 0
        self.line = 1
        self.column = 1
        self.length = len(text)

    def _current_char(self) -> Optional[str]:
        if self.pos >= self.length:
            return None
        return self.text[self.pos]

    def _advance(self):
        ch = self._current_char()
        if ch == '\n':
            self.line += 1
            self.column = 1
        else:
            self.column += 1
        self.pos += 1

    def _peek(self) -> Optional[str]:
        if self.pos + 1 >= self.length:
            return None
        return self.text[self.pos + 1]

    def _skip_whitespace(self):
        while True:
            ch = self._current_char()
            if ch is not None and ch in (' ', '\t', '\r', '\n'):
                self._advance()
            else:
                break

    def _skip_comment(self):
        # // ile başlayan tek satırlık yorumu atla
        while True:
            ch = self._current_char()
            if ch is None or ch == '\n':
                break
            self._advance()

    def _identifier_or_keyword(self) -> Token:
        start_line = self.line
        start_column = self.column
        result = []
        ch = self._current_char()
        while ch is not None and (ch.isalpha() or ch.isdigit() or ch == '_'):
            result.append(ch)
            self._advance()
            ch = self._current_char()
        text = "".join(result)
        token_type = KEYWORDS.get(text, "ID")
        return Token(token_type, text, start_line, start_column)

    def _number(self) -> Token:
        start_line = self.line
        start_column = self.column
        result = []
        ch = self._current_char()
        while ch is not None and ch.isdigit():
            result.append(ch)
            self._advance()
            ch = self._current_char()
        text = "".join(result)
        return Token("NUMBER", text, start_line, start_column)

    def get_tokens(self) -> List[Token]:
        tokens: List[Token] = []

        while True:
            self._skip_whitespace()
            ch = self._current_char()
            if ch is None:
                break

            # Yorum: //
            if ch == '/' and self._peek() == '/':
                # '//' karakterlerini de tüket
                self._advance()
                self._advance()
                self._skip_comment()
                continue

            # Identifier veya Keyword
            if ch.isalpha() or ch == '_':
                tokens.append(self._identifier_or_keyword())
                continue

            # Sayı
            if ch.isdigit():
                tokens.append(self._number())
                continue

            # Tek karakterli semboller
            if ch in SINGLE_CHAR_TOKENS:
                token_type = SINGLE_CHAR_TOKENS[ch]
                token = Token(token_type, ch, self.line, self.column)
                self._advance()
                tokens.append(token)
                continue

            # Tanımsız karakter
            raise LexerError(
                f"Lexical error at line {self.line}, column {self.column}: "
                f"unexpected character {ch!r}"
            )

        tokens.append(Token("EOF", "", self.line, self.column))
        return tokens


# PARSER + LEFTMOST DERIVATION

class Parser:
    """
    LL(1) Recursive Descent Parser
    Gramer:

    Program   → DeclList StmtList

    DeclList  → Decl DeclList | ε
    Decl      → INT ID SEMICOLON

    StmtList  → Stmt StmtList | ε
    Stmt      → ID ASSIGN Expr SEMICOLON
              | PRINT LPAREN ID RPAREN SEMICOLON

    Expr      → Term ExprPrime
    ExprPrime → PLUS Term ExprPrime
              | MINUS Term ExprPrime
              | ε

    Term      → Factor TermPrime
    TermPrime → MULT Factor TermPrime
              | DIV Factor TermPrime
              | ε

    Factor    → ID
              | NUMBER
              | LPAREN Expr RPAREN
    """

    def __init__(self, tokens: List[Token]):
        self.tokens = tokens
        self.pos = 0
        self.current = self.tokens[self.pos]
        # Leftmost derivation için
        self.sentential_form: List[str] = ["Program"]
        self.derivation_steps: List[str] = ["Program"]  # 1. adım: sadece başlangıç sembolü

    # ---- Yardımcılar ----

    def _advance(self):
        if self.current.type != "EOF":
            self.pos += 1
            self.current = self.tokens[self.pos]

    def _match(self, token_type: str):
        if self.current.type == token_type:
            self._advance()
        else:
            raise ParserError(
                f"Syntax error at line {self.current.line}, near token "
                f"{self.current.type} (value {self.current.value!r}) - "
                f"expected {token_type}"
            )

    def _record_derivation(self, nonterminal: str, rhs: List[str]):
        """
        Soldan türetim için:
        sentential_form: örn ['Program']
        nonterminal: örn 'Program'
        rhs: örn ['DeclList', 'StmtList']  (ε üretimi için ['ε'] kullanabiliriz)
        """
        try:
            idx = self.sentential_form.index(nonterminal)
        except ValueError:
            # Nonterminal şu an sentential formda
            return

        if rhs == ["ε"]:
            # epsilon üretimi → nonterminal silinir
            new_form = (
                self.sentential_form[:idx] +
                self.sentential_form[idx + 1:]
            )
        else:
            new_form = (
                self.sentential_form[:idx] +
                rhs +
                self.sentential_form[idx + 1:]
            )
        self.sentential_form = new_form
        self.derivation_steps.append(" ".join(self.sentential_form))

    # ---- Gramer Fonksiyonları ----

    def parse(self):
        self.parse_program()
        if self.current.type != "EOF":
            raise ParserError(
                f"Syntax error: extra input after valid program at "
                f"line {self.current.line}, token {self.current}"
            )

    def parse_program(self):
        # Program → DeclList StmtList
        self._record_derivation("Program", ["DeclList", "StmtList"])
        self.parse_decl_list()
        self.parse_stmt_list()

    def parse_decl_list(self):
        # DeclList → Decl DeclList | ε
        if self.current.type == "INT":
            self._record_derivation("DeclList", ["Decl", "DeclList"])
            self.parse_decl()
            self.parse_decl_list()
        else:
            # epsilon üretimi
            self._record_derivation("DeclList", ["ε"])
            # boş dönüş

    def parse_decl(self):
        # Decl → INT ID SEMICOLON
        self._record_derivation("Decl", ["int", "id", ";"])
        self._match("INT")
        self._match("ID")
        self._match("SEMICOLON")

    def parse_stmt_list(self):
        # StmtList → Stmt StmtList | ε
        if self.current.type in ("ID", "PRINT"):
            self._record_derivation("StmtList", ["Stmt", "StmtList"])
            self.parse_stmt()
            self.parse_stmt_list()
        else:
            # epsilon
            self._record_derivation("StmtList", ["ε"])
            # boş

    def parse_stmt(self):
        # Stmt → ID ASSIGN Expr SEMICOLON
        #      | PRINT LPAREN ID RPAREN SEMICOLON
        if self.current.type == "ID":
            self._record_derivation("Stmt", ["id", "=", "Expr", ";"])
            self._match("ID")
            self._match("ASSIGN")
            self.parse_expr()
            self._match("SEMICOLON")
        elif self.current.type == "PRINT":
            self._record_derivation("Stmt", ["print", "(", "id", ")", ";"])
            self._match("PRINT")
            self._match("LPAREN")
            self._match("ID")
            self._match("RPAREN")
            self._match("SEMICOLON")
        else:
            raise ParserError(
                f"Syntax error at line {self.current.line}: expected ID or PRINT, "
                f"found {self.current.type}"
            )

    def parse_expr(self):
        # Expr → Term ExprPrime
        self._record_derivation("Expr", ["Term", "ExprPrime"])
        self.parse_term()
        self.parse_expr_prime()

    def parse_expr_prime(self):
        # ExprPrime → PLUS Term ExprPrime
        #           | MINUS Term ExprPrime
        #           | ε
        if self.current.type == "PLUS":
            self._record_derivation("ExprPrime", ["+", "Term", "ExprPrime"])
            self._match("PLUS")
            self.parse_term()
            self.parse_expr_prime()
        elif self.current.type == "MINUS":
            self._record_derivation("ExprPrime", ["-", "Term", "ExprPrime"])
            self._match("MINUS")
            self.parse_term()
            self.parse_expr_prime()
        else:
            # ε
            self._record_derivation("ExprPrime", ["ε"])

    def parse_term(self):
        # Term → Factor TermPrime
        self._record_derivation("Term", ["Factor", "TermPrime"])
        self.parse_factor()
        self.parse_term_prime()

    def parse_term_prime(self):
        # TermPrime → MULT Factor TermPrime
        #           | DIV Factor TermPrime
        #           | ε
        if self.current.type == "MULT":
            self._record_derivation("TermPrime", ["*", "Factor", "TermPrime"])
            self._match("MULT")
            self.parse_factor()
            self.parse_term_prime()
        elif self.current.type == "DIV":
            self._record_derivation("TermPrime", ["/", "Factor", "TermPrime"])
            self._match("DIV")
            self.parse_factor()
            self.parse_term_prime()
        else:
            # ε
            self._record_derivation("TermPrime", ["ε"])

    def parse_factor(self):
        # Factor → ID
        #        | NUMBER
        #        | LPAREN Expr RPAREN
        if self.current.type == "ID":
            self._record_derivation("Factor", ["id"])
            self._match("ID")
        elif self.current.type == "NUMBER":
            self._record_derivation("Factor", ["number"])
            self._match("NUMBER")
        elif self.current.type == "LPAREN":
            self._record_derivation("Factor", ["(", "Expr", ")"])
            self._match("LPAREN")
            self.parse_expr()
            self._match("RPAREN")
        else:
            raise ParserError(
                f"Syntax error at line {self.current.line}: expected ID, NUMBER, or '(', "
                f"found {self.current.type}"
            )


# MAIN

def main():
    if len(sys.argv) < 2:
        print("Kullanım: python mini_ll1.py <girdi_dosyasi>")
        print("Örn: python mini_ll1.py ornek.mini")
        sys.exit(1)

    filename = sys.argv[1]
    try:
        with open(filename, "r", encoding="utf-8") as f:
            text = f.read()
    except FileNotFoundError:
        print(f"Hata: '{filename}' dosyası bulunamadı.")
        sys.exit(1)

    try:
        # Lexer
        lexer = Lexer(text)
        tokens = lexer.get_tokens()

        # Token akışı 
        print("=== Token Akışı ===")
        print(" ".join(t.type for t in tokens))

        # Parser
        parser = Parser(tokens)
        parser.parse()

        # Başarılıysa:
        print("\nProgram başarıyla parse edildi.\n")

        # Soldan türetim adımları
        print("=== Soldan Türetim (Leftmost Derivation) Adımları ===")
        for i, step in enumerate(parser.derivation_steps, start=1):
            print(f"{i:2d}) {step}")

    except LexerError as e:
        print(str(e))
        sys.exit(1)
    except ParserError as e:
        print(str(e))
        sys.exit(1)


if __name__ == "__main__":
    main()
