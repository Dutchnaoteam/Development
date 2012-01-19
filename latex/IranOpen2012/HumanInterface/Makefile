FILE = HumanInterface

all: article

article:
	pdflatex ${FILE}
	bibtex ${FILE}
	pdflatex ${FILE}
	pdflatex ${FILE}
#	makeindex ICCS2002article156
#	latex ICCS2002article156
#	dvipdf ${FILE}

draft:
	pdflatex ${FILE}
#	dvipdf ${FILE}

tar:
	tar cvf ${FILE}.tar ${FILE}.tex *.bib images/*.png *.cls *.sty *.bst Makefile
	gzip ${FILE}.tar

zip:
	zip ${FILE}.zip ${FILE}.tex *.bib *.png *.cls *.sty *.bst Makefile

clean:
	rm -f *.aux *.log *.dvi *.toc *.lof *.lot *.tmp *.idx *.ilg *.ind *.blg

public:
	install ${FILE}.pdf ~/public_html/publications/
