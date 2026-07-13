require xorg-lib-common.inc

# libxpm requires xgettext to build
inherit gettext ptest

SUMMARY = "Xpm: X Pixmap extension library"

DESCRIPTION = "libXpm provides support and common operation for the XPM \
pixmap format, which is commonly used in legacy X applications.  XPM is \
an extension of the monochrome XBM bitmap specificied in the X \
protocol."

LICENSE = "MIT"
LIC_FILES_CHKSUM = "file://COPYING;md5=903942ebc9d807dfb68540f40bae5aff"
DEPENDS += "libxext libsm libxt gettext-native"
DEPENDS += "${@bb.utils.contains('DISTRO_FEATURES', 'ptest', 'glib-2.0', '', d)}"
PE = "1"

XORG_PN = "libXpm"
EXTRA_OECONF += "--disable-open-zfile"
EXTRA_OECONF += "${@bb.utils.contains('DISTRO_FEATURES', 'ptest', '--enable-unit-tests', '--disable-unit-tests', d)}"

PACKAGES =+ "sxpm cxpm"
FILES:cxpm = "${bindir}/cxpm"
FILES:sxpm = "${bindir}/sxpm"

SRC_URI += " file://run-ptest"

SRC_URI[sha256sum] = "ad3576d689221a39dc728f0e0dc02ca7bb6a0d724c9a77fd1bfa1e9af83be900"

TEST_TARGETS = "XpmCreate XpmMisc XpmRead XpmWrite rgb"

do_compile_ptest() {
    oe_runmake -C ${B}/test ${TEST_TARGETS}
}

do_install_ptest() {
    for test_bin in ${TEST_TARGETS}; do
        ${B}/libtool --mode=install install ${B}/test/${test_bin} ${D}${PTEST_PATH}/
    done

    cp -r ${S}/test/pixmaps ${D}${PTEST_PATH}/

    install -m 0644 ${S}/test/rgb.txt ${D}${PTEST_PATH}/
}

BBCLASSEXTEND = "native"
