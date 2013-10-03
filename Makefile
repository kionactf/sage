# Main Makefile for Sage.

# The default target ("all") builds Sage and the whole (HTML) documentation.
#
# Target "build" just builds Sage.
#
# See below for targets to build the documentation in other formats,
# to run various types of test suites, and to remove parts of the build etc.

PIPE = build/pipestatus

all: start doc  # indirectly depends on build

logs:
	mkdir -p $@

build: logs
	cd build && \
	"../$(PIPE)" \
		"env SAGE_PARALLEL_SPKG_BUILD='$(SAGE_PARALLEL_SPKG_BUILD)' ./install all 2>&1" \
		"tee -a ../logs/install.log"
	./sage -b

# Preemptively download all standard upstream source tarballs.
download:
	export SAGE_ROOT=$$(pwd) && \
	export PATH=$$SAGE_ROOT/src/bin:$$PATH && \
	./src/bin/sage-download-upstream

# ssl: build Sage, and also install pyOpenSSL. This is necessary for
# running the secure notebook. This make target requires internet
# access. Note that this requires that your system have OpenSSL
# libraries and headers installed. See README.txt for more
# information.
ssl: all
	./sage -i pyopenssl

build-serial: SAGE_PARALLEL_SPKG_BUILD = no
build-serial: build

# Start Sage if the file local/etc/sage-started.txt does not exist
# (i.e. when we just installed Sage for the first time).
start: build
	[ -f local/etc/sage-started.txt ] || local/bin/sage-starts

# You can choose to have the built HTML version of the documentation link to
# the PDF version. To do so, you need to build both the HTML and PDF versions.
# To have the HTML version link to the PDF version, do
#
# $ ./sage --docbuild all html
# $ ./sage --docbuild all pdf
#
# For more information on the docbuild utility, do
#
# $ ./sage --docbuild -H
doc: doc-html

doc-html: build
	$(PIPE) "./sage --docbuild --no-pdf-links all html $(SAGE_DOCBUILD_OPTS) 2>&1" "tee -a logs/dochtml.log"

doc-html-mathjax: build
	$(PIPE) "./sage --docbuild --no-pdf-links all html -j $(SAGE_DOCBUILD_OPTS) 2>&1" "tee -a logs/dochtml.log"

# Keep target 'doc-html-jsmath' for backwards compatibility.
doc-html-jsmath: doc-html-mathjax

doc-pdf: build
	$(PIPE) "./sage --docbuild all pdf $(SAGE_DOCBUILD_OPTS) 2>&1" "tee -a logs/docpdf.log"

doc-clean:
	cd src/doc && $(MAKE) clean

clean:
	@echo "Deleting package build directories..."
	rm -rf local/var/tmp/sage/build

lib-clean:
	cd src && $(MAKE) clean

bdist-clean: clean
	@echo "Deleting miscellaneous artifacts generated by build system ..."
	rm -rf logs
	rm -rf dist
	rm -rf tmp
	rm -f build/Makefile
	rm -f .BUILDSTART

distclean: clean doc-clean lib-clean bdist-clean
	@echo "Deleting all remaining output from build system ..."
	rm -rf local

micro_release: bdist-clean lib-clean
	@echo "Stripping binaries ..."
	LC_ALL=C find local/lib local/bin -type f -exec strip '{}' ';' 2>&1 | grep -v "File format not recognized" |  grep -v "File truncated" || true

TESTPRELIMS = local/bin/sage-starts
TESTALL = ./sage -t --all
PTESTALL = ./sage -t -p --all

test: all # i.e. build and doc
	$(TESTPRELIMS)
	$(TESTALL) --logfile=logs/test.log

check: test

testall: all # i.e. build and doc
	$(TESTPRELIMS)
	$(TESTALL) --optional=all --logfile=logs/testall.log

testlong: all # i.e. build and doc
	$(TESTPRELIMS)
	$(TESTALL) --long --logfile=logs/testlong.log

testalllong: all # i.e. build and doc
	$(TESTPRELIMS)
	$(TESTALL) --long --optional=all --logfile=logs/testalllong.log

ptest: all # i.e. build and doc
	$(TESTPRELIMS)
	$(PTESTALL) --logfile=logs/ptest.log

ptestall: all # i.e. build and doc
	$(TESTPRELIMS)
	$(PTESTALL) --optional=all --logfile=logs/ptestall.log

ptestlong: all # i.e. build and doc
	$(TESTPRELIMS)
	$(PTESTALL) --long --logfile=logs/ptestlong.log

ptestalllong: all # i.e. build and doc
	$(TESTPRELIMS)
	$(PTESTALL) --long --optional=all --logfile=logs/ptestalllong.log


testoptional: testall # just an alias

testoptionallong: testalllong # just an alias

ptestoptional: ptestall # just an alias

ptestoptionallong: ptestalllong # just an alias


install:
	echo "Experimental use only!"
	if [ "$(DESTDIR)" = "" ]; then \
		echo >&2 "Set the environment variable DESTDIR to the install path."; \
		exit 1; \
	fi
	# Make sure we remove only an existing directory. If $(DESTDIR)/sage is
	# a file instead of a directory then the mkdir statement later will fail
	if [ -d "$(DESTDIR)"/sage ]; then \
		rm -rf "$(DESTDIR)"/sage; \
	fi
	mkdir -p "$(DESTDIR)"/sage
	mkdir -p "$(DESTDIR)"/bin
	cp -Rp * "$(DESTDIR)"/sage
	rm -f "$(DESTDIR)"/bin/sage
	ln -s ../sage/sage "$(DESTDIR)"/bin/sage
	"$(DESTDIR)"/bin/sage -c # Run sage-location


.PHONY: all build build-serial start install \
	doc doc-html doc-html-jsmath doc-html-mathjax doc-pdf \
	doc-clean clean lib-clean bdist-clean distclean micro_release \
	test check testoptional testall testlong testoptionallong testallong \
	ptest ptestoptional ptestall ptestlong ptestoptionallong ptestallong
