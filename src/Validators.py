import math
from PyQt5.QtGui import QValidator
import re

class UniversalNumericListValidator(QValidator):

    def __init__(self,
                 schema=("float",),
                 max_items=None,
                 allow_negative=True,
                 allow_pi=True,
                 allow_zero=True,
                 parent=None):

        super().__init__(parent)

        self.schema = list(schema)
        self.max_items = max_items
        self.allow_negative = allow_negative
        self.allow_pi = allow_pi
        self.allow_zero = allow_zero

        self.pattern = re.compile(r'[,\s;:]+')

        # FLOAT (scientific OK)
        self.float_re = re.compile(
            r'^[+-]?('
            r'(\d+(?:\.\d*)?)|'
            r'(\.\d+)'
            r')([eE][+-]?\d+)?$'
        )

        #FLOAT = r'(?:\d+(?:\.\d*)?|\.\d*)'

        FLOAT = (
            r'(?:'
            r'(?:\d+(?:\.\d*)?|\.\d+)'
            r'(?:[eE][+-]?\d+)?'
            r')'
        )

        self.pi_complete_re = re.compile(
            rf'^[+-]?(?:'
            rf'pi'
            rf'|[+-]pi'
            rf'|{FLOAT}\*?pi'
            rf'|pi\*?{FLOAT}'
            rf'|pi/{FLOAT}'
            rf')$'
        )

    # ================= FLOAT =================
    def _is_float(self, p):
        return bool(self.float_re.match(p))

    def _is_intermediate_float(self, p):
        return p.endswith(('e', 'e-', 'e+'))

    # ================= PI =================
    def _is_complete_pi(self, p):
        if not self.allow_pi:
            return False
        if not self.allow_negative and p.startswith('-'):
            return False
        return bool(self.pi_complete_re.match(p))

    def _is_intermediate_pi1(self, p):
        if not self.allow_pi:
            return False

        # block negative ONLY if leading and not allowed
        if not self.allow_negative and p.startswith('-'):
            return False

        FLOAT_BASE = r'(?:\d+(?:\.\d*)?|\.\d*)'

        if p in ('p', 'pi', 'pi/', 'pi*'):
            return True

        if re.match(rf'^{FLOAT_BASE}p$', p):
            return True

        if re.match(rf'^{FLOAT_BASE}\*$', p):
            return True

        if re.match(rf'^{FLOAT_BASE}\*p$', p):
            return True

        if re.match(rf'^pi{FLOAT_BASE}$', p):
            return True

        if re.match(rf'^pi\*{FLOAT_BASE}$', p):
            return True

        if re.match(rf'^pi/{FLOAT_BASE}$', p):
            return True

        return False

    def _is_intermediate_pi(self, p):
        if not self.allow_pi:
            return False

        # -------- handle optional leading sign --------
        sign = ''
        core = p

        if p.startswith('-'):
            if not self.allow_negative:
                return False
            sign = '-'
            core = p[1:]
        elif p.startswith('+'):
            sign = '+'
            core = p[1:]

        #FLOAT_BASE = r'(?:\d+(?:\.\d*)?|\.\d*)'

        FLOAT_BASE = (
            r'(?:'
            r'(?:\d+(?:\.\d*)?|\.\d+)'
            r'(?:[eE][+-]?\d*)?'
            r')'
        )
        
        # -------- simple partial tokens --------
        if core in ('p', 'pi', 'pi/', 'pi*'):
            return True

        # 2p
        if re.match(rf'^{FLOAT_BASE}p$', core):
            return True

        # 2*
        if re.match(rf'^{FLOAT_BASE}\*$', core):
            return True

        # 2*p
        if re.match(rf'^{FLOAT_BASE}\*p$', core):
            return True

        # pi2 / pi2.5
        if re.match(rf'^pi{FLOAT_BASE}$', core):
            return True

        # pi*2
        if re.match(rf'^pi\*{FLOAT_BASE}$', core):
            return True

        # pi/2
        if re.match(rf'^pi/{FLOAT_BASE}$', core):
            return True

        return False

    # ================= INT =================
    def _is_valid_int(self, p):
        if not re.match(r'^[+-]?\d+$', p):
            return False
        val = int(p)
        return val >= 0 if self.allow_zero else val > 0

    def _is_pos_int(self, p):
        return p.isdigit() and int(p) > 0

    # ================= VALIDATE =================
    def validate(self, input_str, pos):

        if not input_str.strip():
            return QValidator.Intermediate, input_str, pos

        parts = self.pattern.split(input_str.strip())

        if self.max_items is not None and len(parts) > self.max_items:
            return QValidator.Invalid, input_str, pos

        for i, part in enumerate(parts):

            if not part:
                return QValidator.Intermediate, input_str, pos

            p = part.strip().lower()
            expected = self.schema[min(i, len(self.schema) - 1)]
            is_last = (i == len(parts) - 1)

            # -------- FLOAT --------
            if expected == "float":

                # 🚨 Prevent scientific exponent from starting an entry
                if p in ("E", "e", "+E", "+e", "-E", "-e"):
                    return (QValidator.Invalid, input_str, pos)

                if p.startswith(("E", "e", "+E", "+e", "-E", "-e")):
                    return (QValidator.Invalid, input_str, pos)

                # 🚨 block ONLY leading minus if not allowed
                if not self.allow_negative and p.startswith('-'):
                    return QValidator.Invalid, input_str, pos

                # allow typing "-"" if negatives allowed
                if p == '-' and self.allow_negative:
                    return QValidator.Intermediate, input_str, pos

                if p == '+':
                    return QValidator.Intermediate, input_str, pos

                # scientific typing
                if is_last and self._is_intermediate_float(p):
                    return QValidator.Intermediate, input_str, pos

                # pi typing
                if is_last and self._is_intermediate_pi(p):
                    return QValidator.Intermediate, input_str, pos

                # final valid
                if self._is_float(p) or self._is_complete_pi(p):
                    continue

                return QValidator.Invalid, input_str, pos
            


            # -------- INT --------
            elif expected == "int":

                if not self.allow_negative and p.startswith('-'):
                    return QValidator.Invalid, input_str, pos

                if is_last and p in ('-', '+'):
                    return QValidator.Intermediate, input_str, pos

                if not self._is_valid_int(p):
                    return QValidator.Invalid, input_str, pos

            # -------- POS INT --------
            elif expected == "pos_int":

                if p.startswith('-'):
                    return QValidator.Invalid, input_str, pos

                if is_last and p == '+':
                    return QValidator.Intermediate, input_str, pos

                if not self._is_pos_int(p):
                    return QValidator.Invalid, input_str, pos

            else:
                return QValidator.Invalid, input_str, pos

        if len(parts) < len(self.schema):
            return QValidator.Intermediate, input_str, pos

        return QValidator.Acceptable, input_str, pos
