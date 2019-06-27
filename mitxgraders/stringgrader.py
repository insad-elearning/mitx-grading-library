"""
stringgrader.py

Class for grading inputs that correspond to a text string
* StringGrader
"""
import re
from voluptuous import Required, Any
from mitxgraders.baseclasses import ItemGrader
from mitxgraders.helpers.validatorfuncs import NonNegative
from mitxgraders.exceptions import InvalidInput, ConfigError

# Set the objects to be imported from this grader
__all__ = ["StringGrader"]

class StringGrader(ItemGrader):
    """
    Grader based on exact comparison of strings

    Configuration options:
        case_sensitive (bool): Whether to be case sensitive in comparing responses to
            answers (default True)


        clean_spaces (bool): Whether or not to convert multiple spaces into single spaces
            before comparing (default True)

        strip (bool): Whether or not to strip leading and trailing whitespace
            from answers/student input before comparing (default True)

        strip_all (bool): Whether or not to remove all spaces from student
            input before grading (default False)


        accept_any (bool): Whether to accept any answer as correct (default False)

        accept_nonempty (bool): Whether to accept any nonempty answer as correct.
            Implemented as turning on accept_any and ensuring that min_length > 0.
            (default False)


        min_length (int): When using accept_any or accept_nonempty, sets the minimum
            number of characters required to be entered in order to be graded
            correct (default 0)

        min_words (int): When using accept_any or accept_nonempty, sets the minimum
            number of words required to be entered in order to be graded
            correct (default 0)

        explain_minimums (bool): If a response is unsatisfactory due to min_length or
            min_words being insufficient, presents an explanatory message to the student
            (default True)


        validation_pattern (str or None): A regex pattern to validate the cleaned input
            against. If the pattern is not satisfied, the setting in validation_err
            is followed. Applies even when accept_any/accept_nonempty are True.
            (default None)

        validation_err (bool): Whether to raise an error if the validation_pattern
            is not met (True) or to just grade as incorrect (False). If an error is
            raised, invalid_msg is presented to students. When set to True, if debug is
            also set to true, then a message is provided explaining that validation
            failed. (default True)

        invalid_msg (str): Error message presented to students if their input does
            not satisfy the validation pattern
            (default 'Your input is not in the expected format')
    """

    @property
    def schema_config(self):
        """Define the configuration options for StringGrader"""
        # Construct the default ItemGrader schema
        schema = super(StringGrader, self).schema_config
        # Append options
        return schema.extend({
            Required('case_sensitive', default=True): bool,
            Required('strip', default=True): bool,
            Required('strip_all', default=False): bool,
            Required('clean_spaces', default=True): bool,
            Required('accept_any', default=False): bool,
            Required('accept_nonempty', default=False): bool,
            Required('min_length', default=0): NonNegative(int),
            Required('min_words', default=0): NonNegative(int),
            Required('explain_minimums', default=True): bool,
            Required('validation_pattern', default=None): Any(str, None),
            Required('validation_err', default=True): bool,
            Required('invalid_msg', default='Your input is not in the expected format'): str
            })

    def clean_input(self, input):
        """
        Performs cleaning operations on the given input, according to
        case_sensitive, strip, strip_all and clean_spaces.

        Also converts tabs and newlines spaces for the purpose of grading.
        """
        cleaned = str(input)

        # Convert \t and newline characters (\r and \n) to spaces
        # Note: there is no option for this conversion
        cleaned = cleaned.replace('\t', ' ')
        cleaned = cleaned.replace('\r\n', ' ')
        cleaned = cleaned.replace('\n\r', ' ')
        cleaned = cleaned.replace('\r', ' ')
        cleaned = cleaned.replace('\n', ' ')

        # Apply case sensitivity
        if not self.config['case_sensitive']:
            cleaned = cleaned.lower()

        # Apply strip, strip_all and clean_spaces
        if self.config['strip']:
            cleaned = cleaned.strip()
        if self.config['strip_all']:
            cleaned = cleaned.replace(' ', '')
        if self.config['clean_spaces']:
            cleaned = re.sub(r' +', ' ', cleaned)

        return cleaned

    def check_response(self, answer, student_input, **kwargs):
        """
        Grades a student response against a given answer

        Arguments:
            answer (str): The answer to compare to
            student_input (str): The student's input passed by edX
        """
        expect = self.clean_input(answer['expect'])
        student = self.clean_input(student_input)
        incorrect_response = {'ok': False, 'grade_decimal': 0, 'msg': ''}

        # Figure out if we are accepting any input,
        # and construct the appropriate minimum length
        accept_any = self.config['accept_any']
        min_length = self.config['min_length']
        if self.config['accept_nonempty']:
            accept_any = True
            if min_length == 0:
                min_length = 1

        # Apply the validation pattern
        if self.config['validation_pattern'] is not None:
            if not accept_any:
                # Make sure that expect matches the pattern
                match = re.match(self.config['validation_pattern'], expect)
                if match is None:
                    # expect doesn't match the required pattern,
                    # so a student can never get this right.
                    # Raise an error!
                    msg = ("The provided answer '{}' does not match the validation pattern "
                           "'{}'").format(answer['expect'], self.config['validation_pattern'])
                    raise ConfigError(msg)

            # Check to see if the student input matches the validation pattern
            match = re.match(self.config['validation_pattern'], student)
            if match is None:
                # Either raise an error or grade as incorrect
                if self.config['validation_err']:
                    raise InvalidInput(self.config['invalid_msg'])
                else:
                    if self.config['debug']:
                        incorrect_response['msg'] = 'Validation failed'
                    return incorrect_response

        # Perform the comparison
        if accept_any:
            # Just check the minimums. No comparison to expect.
            # Check for the minimum length
            chars = len(student)
            if chars < min_length:
                if self.config['explain_minimums']:
                    msg = 'Your response is too short ({chars}/{min_length} characters)'
                    incorrect_response['msg'] = msg.format(chars=chars,
                                                           min_length=min_length)
                return incorrect_response

            # Check for minimum word count
            if self.config['min_words'] > 0:
                wordcount = len(student.split())
                if wordcount < self.config['min_words']:
                    if self.config['explain_minimums']:
                        msg = 'Your response is too short ({wordcount}/{min_words} words)'
                        msg = msg.format(wordcount=wordcount, min_words=self.config['min_words'])
                        incorrect_response['msg'] = msg
                    return incorrect_response
        else:
            # Check for a match to expect
            if student != expect:
                return incorrect_response

        # If we got here, everything is correct
        return {
            'ok': answer['ok'],
            'grade_decimal': answer['grade_decimal'],
            'msg': answer['msg']
        }

    def __call__(self, expect, student_input):
        """
        The same as ItemGrader.__call__, except that we accept a None
        entry for expect if accept_any or accept_nonempty are set.
        """
        if expect is None and (self.config['accept_any'] or self.config['accept_nonempty']):
            expect = ""

        return super(StringGrader, self).__call__(expect, student_input)
