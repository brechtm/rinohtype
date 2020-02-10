Contributing
============

Thank you for considering contributing to rinohtype! This document contains
some general information with respect to contributions. Please refer to
DEVELOPING.rst for specific information on running tests etc.


Contributor License Agreement
-----------------------------

Please send your contributions by creating a pull request on GitHub. You will
be asked to agree to the `contributor license agreement`_. Why, you might ask?
In the past, I had plans to sell a commercial version of rinohtype. This
version would basically be the same as the open source version, but with the
addition of a closed-source backend for the DITA format. While I'm no longer
actively pursuing these plans at this point, I would like to keep this option
open. In combination with the Affero GPL, the CLA allows me to include
contributions by others in this commercial version while preventing others from
releasing commercial closed-source versions of rinohtype. Additionally, the
CLA protects the project from legal risks. Since I'm no legal expert, I adapted
the contributor license agreement from `Project Harmony`_. You can find a quick
summary and a detailed walkthrough of the license in the guide_.

.. _contributor license agreement:
       https://gist.github.com/brechtm/6149299f7dc0a837179fa6f15b0f0351

.. _Project Harmony: http://harmonyagreements.org

.. _guide: http://harmonyagreements.org/guide.html


Coding guidelines
-----------------

Please follow the coding style used in the existing codebase, which generally
follows the `PEP 8`_ style guide. Here are the most important rules the
codebase conforms to:

* lines are wrapped at 80 columns

* 4 spaces indentation (no tabs)

* descriptive variable/function/class names (not shortened)

* imports are grouped into sections: standard library, external packages and
  rinohtype modules

* minimize use of external dependencies


.. _PEP 8: https://www.python.org/dev/peps/pep-0008/
