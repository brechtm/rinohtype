# -*- coding: utf-8 -*-
from rfic2009style import *

doc = RFIC2009Paper("template.ps")

##doc.title = "ภ สำเภา	من فضلك Submission Format for RFIC2009 (Title in 18-point Times font)"
doc.title = "Submission Format for RFIC2009 (Title in 18-point Times font)"
doc.author = "J. Clerk Maxwell, Michael Faraday, and André M. Ampère (List authors on this line using 12 point Times font &ndash; use a second line if necessary)"
doc.affiliation = "Microwave Research, City, State/Region, Mail/Zip Code, Country (authors' affiliation(s) listed here in 12 point Times font &ndash; use a second line if necessary)"

doc.abstract = "Use 9 point Times New Roman Bold font for the abstract. Set your line spacing to be 10 points rather than single space. Indent the first line by 0.125 inches and type the word ``Abstract'' in 9 point Times New Roman Bold Italic. This should be followed by two spaces, a long dash (option / shift / minus), two spaces, and then the first word of your abstract (as shown above). Please try to keep the length of your abstract to 100 words or less. Times font is an acceptable substitute for Times New Roman font. After the abstract, you should list a few key words from the IEEE approved ``Index Terms'' LIST that describe your paper. The index terms are used by automated IEEE search engines to quickly locate your paper. Typically, you should list about 5 to 7 key words, in alphabetical order, using 9 point Times New Roman Bold font. An example is shown next."
doc.indexTerms = ["delay filters", "ceramics", "power amplifiers", "delay-lines", "coaxial resonators"]


doc << Heading(1, "Introduction")

# doc << newParagraph()
# doc << "Paragraph 1 text goes here"
# doc << newParagraph()
# doc << "Paragraph 2 text goes here"

##doc << Paragraph() << "Please read " << Bold("through") << " this entire template before you start using it to create your paper! This will save you and the RFIC Committee considerable time, and improve your chances for acceptance. The following information is provided to help you prepare the Initial Submission as well as the Final Paper for submission to RFIC2006. (Many authors submit the same paper for the initial as well as the final submission. This is a common practice. See item #4 below.) A contributor should remember that: 久有归天愿 终过鬼门关 千里来寻归宿 春华变苍颜 到处群魔乱舞 更有妖雾盘绕 暗道入阴间 过了阎王殿 险处不须看"
doc << Paragraph("Please read " + Bold("through") + " this entire template before you start using it to create your paper! This will save you and the RFIC Committee considerable time, and improve your chances for acceptance. The following information is provided to help you prepare the Initial Submission as well as the Final Paper for submission to RFIC2006. (Many authors submit the same paper for the initial as well as the final submission. This is a common practice. See item #4 below.) A contributor should remember that:")

lst = List()

lst.append("Deadlines are " + Em("absolute") + ", don't even ask!")
lst.append("Summaries may not exceed " + Bold("four") + " pages, including all figures, tables, references, etc. Additionally, there is a size limit on the electronic version of all Summaries. In Adobe Portable Document Format (PDF), submissions may not exceed 1 Megabyte.")
lst.append("Acceptance rates have historically run at approximately 50%. There is not sufficient room within the Technical Program to accept all submissions.")
lst.append("Many submitters with previous experience realize that, if their submission is accepted, they will be required to submit a version of their Final Paper to be published in the Symposium Digest. As the Digest paper will be similar in length to the Summary, many contributors opt to prepare their Summary in the format required for the Digest. This template contains the instructions for the proper preparation of such a document.")
lst.append("Although not required, you are encouraged to employ this format. This document is being made available as a template for your convenience. If you elect not to use this template, please remember that you must still adhere to the general guidelines embodied in this document concerning, but not limited to, font size, margin size, page limits, file size, etc. (Note: Starting in 2004, Index Terms are required.)")

##doc << lst


doc << Heading(1, "Overview of the Digest Format")

doc << Paragraph("We are requesting that you follow these guidelines as closely as possible so that the Digest has a professional look and resembles the MTT Transactions. All paragraphs of text, including the abstract, figure captions, and references, should be justified at the left " + Em("and the right") + " edges.")

doc << Paragraph("For the Title use 18-point Times (Roman) font. Its paragraph description should be set so that the line spacing is single with 6-point spacing before and 6-point spacing after (Format&rarr;Paragraph&rarr;Indents and Spacing). The font description for the Author List and Authors' Affiliation(s) should be 12-point Times. The paragraph descriptions should be set so that the line spacing is single with 6-point spacings before and after. Use an additional line spacing of 12 points before the beginning of the double column section, as shown above.")

doc << Heading(1, "Detailed Text Formatting")

doc << Paragraph("Using 8.5&times;11-inch paper, the top and bottom margins are 1.125 inches, and the left and right margins are 0.85 inches. Except for Title, Authors and Affiliations, use a double column format. The column width is 3.275 inches and the column spacing is 0.25 inch.")

doc << Paragraph("Each major section begins with a Heading in 10 point Times font centered within the column and numbered using Roman numerals (except for @S Acknowledgement and @S References), followed by a period, a single space, and the title using an initial capital letter for each word. The remaining letters are in @S { small capitals }. The paragraph description of the section heading line should be set for 18 points before, 6 points after, and the line spacing should be set to exactly 12 points.")

doc << Paragraph("For the body of your paper, use 10-point Times font and set your line spacing at \"exactly 12 points\" with 0 points before and after. Indent each paragraph by 0.125 inches.")

doc << Paragraph("Further details are provided in the remainder of this paper for specific situations.")

##doc << Heading(2, "Subheading 1b")
##
##doc << Heading(1, "Heading 2")
##doc << Heading(2, "Subheading 2a")

#fig1 = Figure("bla.eps", "caption")
#doc << Paragraph("reference to " + Ref(fig1) + ".")

doc.render()
