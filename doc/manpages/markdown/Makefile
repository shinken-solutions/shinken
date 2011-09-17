

SRC= $(wildcard *.8.md)
OBJ= $(SRC:.8.md=.8)

all: $(OBJ)

%.8: %.8.md
	pandoc -s -w man $< -o $@

clean:
	rm -f *.8

