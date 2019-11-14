#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4 nu

import os
import logging

logger = logging.getLogger("worker")

if not logger.hasHandlers():
    logger.setLevel(logging.DEBUG if bool(os.getenv("DEBUG", False)) else logging.INFO)
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("[%(asctime)s: %(levelname)s] %(message)s"))
    logger.addHandler(handler)
