#!/bin/bash

{
    echo '"use strict";'
    echo 'var jslinux_start = (function () {'
    echo 'var PCEmulator;'
    cat utils.js;    echo
    echo 'function include(asd) { if (asd==="cpux86-ta.js") PCEmulator=cpux86_ta(); else PCEmulator=cpux86_std(); }'
    cat term.js;     echo
    cat cpux86.js; echo
    echo 'function cpux86_std() {'
    cat cpux86-std.js; echo
    echo 'return PCEmulator;'
    echo '}'
    echo 'function cpux86_ta() {'
    cat cpux86-ta.js; echo
    echo 'return PCEmulator;'
    echo '}'
    cat jslinux.js ; echo
    echo 'return start;'
    echo '}).call({});'
} > all1.js
