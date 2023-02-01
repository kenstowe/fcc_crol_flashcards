# Script for parsing FCC comercial radio operator exam questions
# Version 1.0
# currently only works for Elements 1 and 3



from tkinter import Tk
from tkinter.filedialog import askopenfilename
import re
from PyPDF2 import PdfFileReader
from os.path import dirname, abspath, basename

import pprint
pp = pprint.PrettyPrinter(width=100, compact=False)





def write_cards_to_file(cards, element_num):
# Example card

# ['<p style="font-size:150%;text-align:left;display:flex;flex-direction:column;align-items:center"> '
# 'What cha nnel would you use to place a call to a shore telephone?<br><br> '
# 'A. Ch-16.<br>B. Ch-70.<br>C. Ch-28.<br>D. Ch-06.</p>',
# 'C', '1-14C6 Element_1']
    
    parent_dir = dirname(dirname(abspath(__file__)))
    new_card_file = parent_dir + '/Element_' + element_num + '_cards.txt'
    print('Writing cards to file: ' + new_card_file)
    
    with open(new_card_file, 'w', encoding='utf-8') as f:
        f.write('#separator:Tab' + '\n')
        f.write('#tags column:3' + '\n')
        f.write('#deck:Element_' + element_num + '\n')
        for card in cards.values():
            f.write(str(card[0]) + '\t'  + str(card[1]) + '\t' + str(card[2]))
            f.write('\n')        



# separate a single list of questions in a list of lists with each question being its own list
def separate_questions(questions_rough):
    first = 0
    q_start = 0
    questions_separated = []
    for i in range(len(questions_rough)):
        if re.match(r'^[0-9]-{0,1}[0-9]{1,3}[A-Z][0-9]*', questions_rough[i]) is not None:
            if first == 0:
                q_start = i
                first = 1
            else:
                questions_separated.append(questions_rough[q_start:i])
                q_start = i 
    
    questions_separated.append(questions_rough[q_start:len(questions_rough)])
                
    return(questions_separated)



def parse_elem_1_3(text, element_num):
    tag1 = 'Element_' + element_num
    tag2 = ''       # key topic
    tag3 = ''       # question number
    cards = {}
    questions_rough = [] # questions and multiple choice answers
    questions_separated = []
    questions_cleaned = []
    for i in range(len(text)):
        text[i] = [line.strip() for line in text[i] if line != ' ']
 
    for page in text:
        tag2 = ''   # each page should only have one tag2
                    # some tag2s are shared over multiple pages
                    # each page has its Key Topic listed
        
        for line in page:
        
            if re.search(r'Key Topic [0-9]{1,3}: ', line, re.IGNORECASE):
                line = line.replace('  ', ' ').replace('-', '').replace('’', '')
                tag2 = re.findall(r'Key Topic [0-9]{1,3}: {1,2}[a-z0-9&():, ]{3,6666660}', 
                        line, re.IGNORECASE)[0].split(' ', 3)[3]
                tag2 = tag2.strip().replace(' ', '_')


            elif re.search(r'FCC Commercial Element|Subelement [A-Z] ', line, re.IGNORECASE):
                pass

            # parse bottom of page Answer Keys into list of question numbers and answers
            elif re.match(r'^Answer', line) is not None:
                remove_list = ['Answer', 'Key', ':']    
                for remove in remove_list:
                    line = line.replace(remove, '')
               
                # split line then remove empty items
                line = line.split(' ')
                line = [i for i in line if i != '']
                    
                # create keys and partial list of values containing Answers and Tags
                for i in range(0, len(line), 2):
                    question_num = re.findall(r'[0-9]{1,3}[A-Z][1-6]', line[i])[0]
                    whole_question_num = element_num + '-' + question_num

                    if whole_question_num not in cards:
                        cards[whole_question_num] = [None , line[i + 1], line[i] + 
                                                    ' Element_' + element_num + ' ' + tag2]
            
            else:
                questions_rough.append(line)
    
    questions_separated = separate_questions(questions_rough)
    
    for question in questions_separated:
        question_temp = []    
        for i in range(len(question)):
                    
            # '-(0,1}' and ':(0,1}' in regex below is because the FCC files occasionally miss punctuation
            if re.match(r'^[0-9]-{0,1}[0-9]{1,3}[A-Z][0-9]*|^[A-D][.]{0,1} [A-Z0-9]*', question[i]) is not None:
                question_temp.append(question[i])

            # check for sentences that run onto next line
            else: 
                # pop last line, then concatenate current and previous line to form complete sentence
                last_line = list.pop(question_temp)
                complete_sentence = last_line + ' ' +  question[i] 
                question_temp.append(complete_sentence)
                

        questions_cleaned.append(question_temp)


    for question in questions_cleaned:
        # split question number and question
        question[0] = question[0].split(' ', 1)
        
        # format complete question and add HTML formatting
        question_complete = ('<p style="font-size:150%;text-align:left;display:flex;flex-direction:column;' +
                            'align-items:center">' + question[0][1] + '<br><br>')
        # some of the multiple choice questions are formatted weird and its hard to make sure every question has 4 well defined answers
        # loop over however the answers are formatted in the question list and concatenate answers to complete question 
        for answer in question[1:]:
            question_complete = (question_complete + answer + '<br>')
        question_complete = (question_complete + r'</p>')

        # some lines are missing the "-" in question number
        # remove from all then insert into correct place for all questions
        question[0][0] = question[0][0].replace('-', '')
        question[0][0] = (question[0][0][0] + '-' + question[0][0][1:])


        cards[question[0][0]][0] = question_complete

    write_cards_to_file(cards, element_num)


def open_and_read_file(filename, element_num):
    text = []
    with open(filename, "rb") as f:
        pdf = PdfFileReader(f)
        num_pages = pdf.numPages

        for i in range(num_pages):
            page = pdf.getPage(i).extractText().split('\n')
            text.append(page)        

        if int(element_num) in [1,3]:
            parse_elem_1_3(text, element_num)
        else:
            print('Script can not parse questions for Element number ' + element_num)
            quit()



def get_file_and_elem_num():
    parent_dir = dirname(dirname(abspath(__file__)))

    Tk().withdraw()
    filename = askopenfilename(initialdir= parent_dir + r'/question_pools/',
                               title= "Select a FCC question pool file:",
                               filetypes=[('pdf file', '*.pdf')])

    if re.match(r'Element[ -_]{0,1}[1-9][A-Z]{0,1}.pdf', basename(filename), re.IGNORECASE) is not None:
        element_num = re.findall(r'Element[ -_]{0,1}[1-9][A-Z]{0,1}', filename)[0][-1:]
        open_and_read_file(filename, element_num)
    else:
        print('Filename does not match Element[ -_]{0,1}[1-9][A-Z]{0,1}.pdf')
        quit()



get_file_and_elem_num()







