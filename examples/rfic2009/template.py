# -*- coding: utf-8 -*-
import sys
sys.path.insert(0, 'C:\Documents and Settings\Veerle\My Documents\code\pyte\trunk')
sys.path.insert(0, 'C:\Documents and Settings\Veerle\My Documents\code\pyte\trunk\psg')
print(sys.path)

from rfic2009style import *

tmpl = RFIC2009Paper("template.ps")

tmpl.title = "Submission Format for RFIC2009 (Title in 18-point Times font)"
tmpl.author = "J. Clerk Maxwell, Michael Faraday, and André M. Ampère (List authors on this line using 12 point Times font -- use a second line if necessary)"
tmpl.affiliation = "Microwave Research, City, State/Region, Mail/Zip Code, Country (authors' affiliation(s) listed here in 12 point Times font -- use a second line if necessary)"

tmpl.abstract = "Use 9 point Times New Roman Bold font for the abstract. Set your line spacing to be 10 points rather than single space. Indent the first line by 0.125 inches and type the word ``Abstract'' in 9 point Times New Roman Bold Italic. This should be followed by two spaces, a long dash (option / shift / minus), two spaces, and then the first word of your abstract (as shown above). Please try to keep the length of your abstract to 100 words or less. Times font is an acceptable substitute for Times New Roman font. After the abstract, you should list a few key words from the IEEE approved ``Index Terms'' LIST that describe your paper. The index terms are used by automated IEEE search engines to quickly locate your paper. Typically, you should list about 5 to 7 key words, in alphabetical order, using 9 point Times New Roman Bold font. An example is shown next."
tmpl.indexTerms = ["delay filters", "ceramics", "power amplifiers", "delay-lines", "coaxial resonators"]


tmpl << Heading(1, "Introduction")

# tmpl << newParagraph()
# tmpl << "Paragraph 1 text goes here"
# tmpl << newParagraph()
# tmpl << "Paragraph 2 text goes here"

tmpl << Paragraph() << "Please read " << Bold("through") << " this entire template before you start using it to create your paper! This will save you and the RFIC Committee considerable time, and improve your chances for acceptance. The following information is provided to help you prepare the Initial Submission as well as the Final Paper for submission to RFIC2006. (Many authors submit the same paper for the initial as well as the final submission. This is a common practice. See item #4 below.) A contributor should remember that:"

##lst = List(ListStyle.Numbered)
##
##lst << ListItem("Deadlines are " + Em("absolute") + ", don't even ask!")
##
##tmpl << lst
##
#tmpl << List(ListStyle.Numbered)
#
#tmpl << ListItem("Deadlines are " + Em("absolute") + ", don't even ask!")
#
#tmpl << ListItem("Summaries may not exceed " + Bold("four") + " pages, including all figures, tables, references, etc. Additionally, there is a size limit on the electronic version of all Summaries. In Adobe Portable Document Format (PDF), submissions may not exceed 1 Megabyte.")

#@ListItem {
#Acceptance rates have historically run at approximately 50%. There is not sufficient room within the Technical Program to accept all submissions.
#}
#@ListItem {
#Many submitters with previous experience realize that, if their submission is accepted, they will be required to submit a version of their Final Paper to be published in the Symposium Digest. As the Digest paper will be similar in length to the Summary, many contributors opt to prepare their Summary in the format required for the Digest. This template contains the instructions for the proper preparation of such a document.
#}
#@ListItem {
#Although not required, you are encouraged to employ this format. This document is being made available as a template for your convenience. If you elect not to use this template, please remember that you must still adhere to the general guidelines embodied in this document concerning, but not limited to, font size, margin size, page limits, file size, etc. (Note: Starting in 2004, Index Terms are required.)
#}
#@End @Section



#fig1 = Figure("bla.eps", "caption")
#tmpl << Paragraph("reference to " + Ref(fig1) + ".")

tmpl << Heading(1, "Detailed Text Formatting")

#tmpl << Paragraph("Using 8.5 @Multiply 11-inch paper, the top and bottom margins are 1.125 inches, and the left and right margins are 0.85 inches. Except for Title, Authors and Affiliations, use a double column format. The column width is 3.275 inches and the column spacing is 0.25 inch.")
#
#tmpl << Paragraph("Each major section begins with a Heading in 10 point Times font centered within the column and numbered using Roman numerals (except for @S Acknowledgement and @S References), followed by a period, a single space, and the title using an initial capital letter for each word. The remaining letters are in @S { small capitals }. The paragraph description of the section heading line should be set for 18 points before, 6 points after, and the line spacing should be set to exactly 12 points.")
#
#tmpl << Paragraph("For the body of your paper, use 10-point Times font and set your line spacing at ``exactly 12 points'' with 0 points before and after. Indent each paragraph by 0.125 inches.")

#tmpl << Paragraph("Further details are provided in the remainder of this paper for specific situations.")

tmpl.render()
