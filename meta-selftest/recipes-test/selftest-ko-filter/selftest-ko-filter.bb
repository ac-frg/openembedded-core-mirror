#
# Copyright OpenEmbedded Contributors
#
# SPDX-License-Identifier: MIT
#
SUMMARY = "Test fixture for the kernel-module file pre-filter in package.py"
LICENSE = "MIT"
LIC_FILES_CHKSUM = "file://${COMMON_LICENSE_DIR}/MIT;md5=0835ade698e0bcf8506ecda2f7b4f302"

SRC_URI = "file://module.c"
S = "${UNPACKDIR}"

MODDIR = "${libdir}/selftest-ko-filter"

do_compile () {
    ${CC} ${CFLAGS} -c module.c -o module.ko
}

do_install () {
    install -d ${D}${MODDIR}
    install -m 0644 module.ko ${D}${MODDIR}/

    # Fake compressed modules — the pre-filter must not pass these to strip.
    # Use octal escapes: dash (the OE recipe shell) does not support \xHH in printf.
    printf '\375\067\172\130\132\000' > ${D}${MODDIR}/module.ko.xz
    printf '\037\213'                 > ${D}${MODDIR}/module.ko.gz
}

FILES:${PN} = "${MODDIR}/*"
