#!/usr/bin/python
# -*- coding: utf-8 -*-
##  This file is part of psg, PostScript Generator.
##
##  Copyright 2006 by Diedrich Vorberg <diedrich@tux4web.de>
##  Copyright 2006 by Andreas Junge <aj@jungepartner.de>
##
##  All Rights Reserved
##
##  For more Information on orm see the README file.
##
##  This program is free software; you can redistribute it and/or modify
##  it under the terms of the GNU General Public License as published by
##  the Free Software Foundation; either version 2 of the License, or
##  (at your option) any later version.
##
##  This program is distributed in the hope that it will be useful,
##  but WITHOUT ANY WARRANTY; without even the implied warranty of
##  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
##  GNU General Public License for more details.
##
##  You should have received a copy of the GNU General Public License
##  along with this program; if not, write to the Free Software
##  Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
##
##  I have added a copy of the GPL in the file gpl.txt.


#
# $Log: lorem_ipsum.py,v $
# Revision 1.1  2006/10/16 12:50:11  diedrich
# Initial commit
#
# Revision 1.1  2006/10/15 18:02:52  t4w00-diedrich
# Initial commit.
#
#
#

from string import *
from random import random


"""
This module will create tons of familiar latin dummy text. The main
function is lorem_ipsum(), see below.
"""

def _words():
    l = []

    while True:
        if len(l) == 0:
            l = splitfields(ipsum)
            l.reverse()

        ret = l.pop()
        ret = lower(ret)

        if ret[-1] == "." or ret[-1] == ",":
            ret = ret[:-1]
        
        yield ret
        
words = _words()

def lorem_ipsum(min, max=None, sentences=False, cap=True):
    """
    @param min: Integer indicating the minimum number of words returned
    @param max: Integer indicating the maximum number of words returned. If
       omited, exactly min number of words will be returned.
    @param sentences: Boolean indicating whether min and max refer to words
       (the default) or sentences.
    @param cap: Boolean indicating whether the first word returned will be
       capitalized.
    """
    if max is None:
        num = min
    else:
        num = min + int(random() * float(max))
        
    ret = []
    
    if sentences:
        for a in range(num):
            sentence = lorem_ipsum(3, 9, cap=True)
            sentence += "."
            ret.append(sentence)
            
    else:
        for a in range(num):
            ret.append(words.next())

        if cap: ret[0] = capitalize(ret[0])
            

    return unicode(join(ret, " "))


class lorem_ipsum_property(property):
    """
    The lorem_ipsum_property can be used in classes to create string
    attributes with random content.
    """
    def __init__(self, min, max=None, sentences=False, cap=True):
        self.min = min
        self.max = max
        self.sentences = sentences
        self.cap = cap

    def __get__(self, instance, owner=None):
        return lorem_ipsum(self.min, self.max, self.sentences, self.cap)

    def __set__(self, instance, value):
        raise Exception("You can't set a lorem_ipsum_property.")
    
         
    

ipsum = """\
Lorem ipsum dolor sit amet, consectetuer adipiscing elit. Pellentesque dapibus vehicula nunc. Duis sagittis. Donec metus tellus, gravida eu, ullamcorper sed, sagittis quis, nisi. Praesent lacinia magna ut arcu. Praesent mattis ipsum at nisl. Lorem ipsum dolor sit amet, consectetuer adipiscing elit. Pellentesque habitant morbi tristique senectus et netus et malesuada fames ac turpis egestas. Pellentesque facilisis lectus vitae mi. Phasellus mattis volutpat massa. Nam mollis purus id est. Fusce in tellus sed arcu sagittis tincidunt. Mauris purus. Quisque commodo imperdiet elit. In lacinia placerat dui. Donec sed urna. Integer arcu ante, feugiat ut, volutpat at, volutpat eget, felis. In volutpat.

Suspendisse eleifend. Cras eu odio at tellus auctor ullamcorper. Praesent vehicula ornare lacus. Nam purus magna, hendrerit quis, pulvinar eu, luctus sit amet, sapien. Nullam quis justo vel enim euismod posuere. Praesent mauris nisi, consequat vel, sollicitudin et, tincidunt a, ligula. Donec felis neque, venenatis et, ultricies tempor, bibendum non, magna. Phasellus euismod. Ut malesuada felis eget est. In euismod. Aliquam at sapien. Etiam aliquet, metus sed pharetra pulvinar, nisi odio tincidunt justo, at dignissim lectus felis eget tellus. Nam blandit. Sed non neque. Pellentesque sit amet enim. Ut ultricies nisi a urna. Nullam volutpat lectus in dolor. Etiam vestibulum, lectus vitae pulvinar imperdiet, leo urna rutrum pede, in faucibus urna massa ac ligula.

Praesent nunc massa, sagittis accumsan, faucibus sit amet, laoreet vel, elit. Pellentesque quis quam. Cras ut lacus. Proin tempor. Maecenas in quam nec lacus hendrerit mollis. Donec posuere, tortor nec malesuada mollis, justo est molestie enim, sed luctus sem ipsum nec ipsum. In at metus non est tristique facilisis. Aliquam erat volutpat. Integer et justo eget enim consectetuer vulputate. Mauris congue ipsum ac orci. Cras nec nibh eu magna vehicula aliquam. Sed pretium sagittis velit. Pellentesque malesuada neque a libero. Quisque suscipit ante quis odio. Vestibulum est quam, cursus eu, vestibulum nec, facilisis et, velit. Sed eu elit.

Maecenas eget mi. Vivamus vulputate, massa luctus feugiat tempus, massa risus lobortis erat, a iaculis velit nisl at sapien. Donec lorem. Nunc egestas tincidunt metus. Sed pulvinar enim vitae quam. Vivamus augue lacus, posuere ac, egestas non, dapibus eu, urna. Cras vulputate ante a lectus. Fusce sodales ante sed diam. Mauris sagittis. Integer auctor nunc vitae tortor. Morbi sapien mauris, dictum sed, molestie sit amet, pellentesque at, ante. Cras pede risus, convallis non, dignissim et, accumsan nec, leo. Sed congue tellus non quam. Nulla facilisi. Nullam at justo.

Quisque suscipit. Morbi porta, neque et egestas tempor, massa est rhoncus odio, ut condimentum odio justo non mauris. Phasellus dignissim mauris. Duis vulputate, arcu nec feugiat ultricies, sapien nulla iaculis turpis, non vehicula nibh nibh non nibh. Sed et sem non urna sollicitudin malesuada. Vivamus enim nunc, nonummy in, adipiscing sagittis, blandit a, dui. Nulla leo. Nunc sit amet augue. Aliquam dignissim, neque vel congue feugiat, metus risus mattis orci, in semper est nisi eget dolor. In pede. Ut magna. Quisque congue pulvinar ligula. In nibh. Nam urna tortor, placerat id, mattis quis, sollicitudin ac, sapien. Praesent nec nulla eget enim accumsan laoreet. Proin convallis pretium pede.

Pellentesque habitant morbi tristique senectus et netus et malesuada fames ac turpis egestas. Nunc sit amet mi a turpis pharetra laoreet. Praesent iaculis, magna non mattis consectetuer, velit dolor ullamcorper urna, et tempus dui tellus mattis velit. Nulla pede. Nunc vel risus eget tortor porta pulvinar. Mauris a nunc. Nulla molestie velit non magna. Aliquam consequat. Mauris ut diam. Nullam pretium pulvinar mi. Mauris non risus sed velit pharetra sagittis. Curabitur mauris. Duis a est. Sed vulputate dolor ac urna. Praesent cursus, enim non eleifend viverra, purus urna adipiscing urna, eget tempor ipsum massa sit amet odio. Mauris eget risus.

Integer at purus sed turpis pretium tincidunt. Vivamus lectus arcu, semper a, hendrerit eu, laoreet vitae, massa. Vivamus sed leo ac risus suscipit viverra. Phasellus turpis est, malesuada ut, laoreet ac, ultrices quis, tortor. Nulla ligula. In sem enim, laoreet sit amet, cursus eu, pulvinar ut, odio. Suspendisse ac massa. Mauris rhoncus tincidunt metus. Nunc non nisi et sapien nonummy iaculis. Donec ac leo vel dui eleifend fermentum. Pellentesque at arcu. Fusce elit purus, porttitor sit amet, sodales quis, feugiat vel, neque. Cum sociis natoque penatibus et magnis dis parturient montes, nascetur ridiculus mus. Mauris dapibus augue nec leo. Suspendisse convallis mattis tortor. Suspendisse nisi.

Nam scelerisque, sem ac tristique commodo, lectus odio aliquet ipsum, quis tristique ante dui id nibh. Lorem ipsum dolor sit amet, consectetuer adipiscing elit. Suspendisse arcu. Maecenas nec mi. Nunc eu enim ac orci placerat consequat. Nam tincidunt rhoncus odio. Suspendisse imperdiet, velit nec fermentum venenatis, est odio aliquet enim, quis imperdiet urna massa vitae dui. Aenean dui. Donec scelerisque, elit vitae scelerisque nonummy, quam felis semper turpis, eu tempus enim ipsum sed libero. Sed rutrum ullamcorper massa. Vestibulum ante sem, ornare in, eleifend sed, mattis sit amet, libero. In hac habitasse platea dictumst. Aliquam nisl magna, suscipit eu, convallis non, vehicula eu, enim. Etiam egestas magna quis tortor sollicitudin sodales.

Ut tortor magna, porttitor a, euismod et, vestibulum ut, ipsum. Quisque mattis. Morbi hendrerit fringilla justo. Sed pretium interdum tellus. Ut magna dolor, rutrum vitae, nonummy et, scelerisque varius, ipsum. Phasellus id nunc. Nunc dictum quam bibendum enim. Maecenas est tortor, ultricies sed, imperdiet id, nonummy in, lectus. Pellentesque eget tellus eu mauris condimentum imperdiet. Curabitur non metus at orci tempor fringilla. Nunc imperdiet, tellus commodo iaculis mattis, enim nibh mollis mi, non blandit felis ipsum vitae lectus. Curabitur sollicitudin mauris vel tellus. Sed ante quam, tincidunt vel, scelerisque ac, semper et, nibh. Ut libero eros, consectetuer ut, cursus quis, cursus sed, mauris.

Nam blandit pharetra erat. Vestibulum a orci sed sem sodales bibendum. Mauris eget est quis lectus elementum fringilla. Aliquam pulvinar. Nam mi lorem, iaculis a, fermentum eget, aliquam eu, velit. Aliquam viverra elit non massa. Cras tincidunt lobortis augue. Donec dapibus, massa sit amet bibendum blandit, lacus mi sollicitudin risus, sit amet posuere neque velit sit amet ante. Maecenas rhoncus, quam quis porttitor congue, tortor urna dictum enim, ac vehicula leo quam bibendum magna. Vestibulum sed erat eu sapien malesuada interdum. Donec egestas fringilla pede.

Morbi in sapien. Suspendisse ornare ligula ut augue. Phasellus quis lorem vitae dui egestas porttitor. Nam nec arcu ut nisi semper tincidunt. Mauris tellus. Integer id leo a velit commodo dictum. Nulla facilisis lobortis tortor. Donec justo. Nulla cursus, lacus at pharetra sollicitudin, est augue cursus risus, id ultricies eros sem vel ligula. Nulla facilisi. Fusce vitae nibh sit amet neque auctor tempus. Duis hendrerit enim ut erat. Phasellus dictum risus aliquam mauris. Praesent elementum. Nunc ipsum metus, egestas eget, eleifend et, convallis quis, tortor. Donec eu velit. Sed leo.

Donec blandit. Curabitur auctor convallis lacus. Praesent scelerisque elementum tellus. Praesent a tellus vel nisi ullamcorper egestas. Mauris nulla libero, luctus nec, nonummy sit amet, dapibus ut, magna. Proin ac felis. Pellentesque nisl. Pellentesque vel velit. Suspendisse viverra, ante quis vulputate convallis, magna ante dignissim sapien, vel venenatis ligula mi eget augue. Morbi vitae tortor. Vivamus mattis elementum arcu. Praesent nec sapien. Morbi nulla. Vivamus pulvinar, tortor non scelerisque rutrum, arcu nisi volutpat ante, eu lacinia nunc erat et augue. Class aptent taciti sociosqu ad litora torquent per conubia nostra, per inceptos hymenaeos.

Mauris aliquet mi eu nibh. Vestibulum mollis lorem ac erat. Praesent velit. Etiam nibh ante, blandit eu, ultricies a, faucibus nec, augue. Class aptent taciti sociosqu ad litora torquent per conubia nostra, per inceptos hymenaeos. Duis laoreet, massa id viverra accumsan, ipsum velit varius orci, eu molestie dui urna vitae ipsum. Donec ullamcorper pulvinar libero. Nunc ac metus. Nam suscipit adipiscing est. Nam sed elit in lectus volutpat sodales. Ut ut orci.

Proin turpis. Nullam id quam sed augue aliquam venenatis. Aliquam nibh lacus, suscipit sit amet, malesuada et, vulputate vitae, purus. Etiam quis nisl. Morbi faucibus massa a lacus mattis tristique. Phasellus pulvinar tempor dolor. Aliquam rutrum. Suspendisse varius elit ac eros. Phasellus nibh sem, dapibus ut, aliquet nec, rhoncus ac, sem. Nulla diam. Pellentesque mattis. Nunc scelerisque lacus ac lorem. Nullam eu lacus a orci condimentum gravida.

Fusce condimentum lacus sit amet erat. Cum sociis natoque penatibus et magnis dis parturient montes, nascetur ridiculus mus. Pellentesque habitant morbi tristique senectus et netus et malesuada fames ac turpis egestas. Fusce mauris dolor, pellentesque et, hendrerit non, sodales et, tortor. Curabitur turpis dolor, pharetra eu, consequat vel, rutrum et, ante. Fusce vel risus. Praesent condimentum. Aenean ultrices imperdiet nisl. Vivamus vestibulum odio id orci. Maecenas feugiat aliquam sem. Sed vel urna et augue laoreet posuere. Nulla ornare iaculis nunc. Quisque consequat iaculis mauris. Nam non dolor non urna aliquet malesuada.

Mauris urna libero, hendrerit in, eleifend convallis, varius eu, ligula. Quisque porta, dolor eu tristique tincidunt, mauris urna tristique urna, quis vulputate tortor diam et libero. Cum sociis natoque penatibus et magnis dis parturient montes, nascetur ridiculus mus. Sed elit nibh, condimentum et, consectetuer et, euismod ut, urna. Nullam elit. Nam hendrerit vestibulum odio. Ut egestas vulputate sapien. Curabitur lacinia laoreet enim. Curabitur tincidunt. Sed semper, quam ac elementum tristique, augue risus adipiscing sem, vulputate rhoncus orci turpis in velit. Fusce mollis dapibus elit. Pellentesque elementum consequat nibh. Donec dapibus, massa et sollicitudin condimentum, orci metus venenatis orci, id cursus dui purus eu felis.

In hac habitasse platea dictumst. Praesent ultricies. Morbi eleifend pellentesque turpis. Vestibulum hendrerit magna sit amet metus. Sed consequat sodales urna. Vivamus augue massa, pretium ut, commodo in, luctus sit amet, arcu. Proin fringilla est sit amet tortor. Nunc ac sapien. Praesent nec libero a enim laoreet dictum. Aenean ornare ultrices libero. Sed commodo nunc vel massa. Nullam adipiscing. Aenean viverra metus sit amet nibh. Nulla viverra orci ac est. Pellentesque diam ipsum, mollis eget, molestie nec, luctus ac, turpis. In dui neque, scelerisque sed, elementum non, consequat sed, sapien. Pellentesque scelerisque diam sed quam. Nulla risus.

Duis eros metus, placerat vel, egestas vitae, sodales ut, sapien. Nullam imperdiet, enim in pretium congue, turpis ipsum gravida lectus, sed tempor urna ante a mauris. Class aptent taciti sociosqu ad litora torquent per conubia nostra, per inceptos hymenaeos. Nulla molestie dignissim est. Integer faucibus, nunc in semper consequat, risus nisi adipiscing massa, eu vehicula sem mauris quis massa. Fusce eget erat ac ligula cursus placerat. Donec elementum nibh quis velit. Sed ultrices. Ut mauris. Integer ullamcorper, urna vitae porta euismod, magna nisi eleifend nulla, eu ullamcorper sapien libero quis lorem. Pellentesque habitant morbi tristique senectus et netus et malesuada fames ac turpis egestas. Nunc pharetra leo id tortor. Vestibulum ante ipsum primis in faucibus orci luctus et ultrices posuere cubilia Curae;

Morbi dolor. Donec ac pede. Suspendisse faucibus purus eget lorem. Donec vulputate. Vivamus diam mauris, adipiscing eu, molestie vel, euismod quis, est. In semper, turpis sit amet consectetuer commodo, orci quam ullamcorper tellus, vulputate egestas ante neque eu mauris. Vivamus convallis metus ac tellus. Suspendisse sed elit a dolor vestibulum pellentesque. Pellentesque molestie. In hac habitasse platea dictumst. Morbi luctus fermentum diam. Donec vulputate, eros sed gravida aliquet, nisi lacus faucibus elit, vel tincidunt sapien velit nonummy enim. Integer fringilla sagittis eros.

Curabitur gravida, nunc dignissim suscipit ornare, est leo consectetuer erat, a laoreet justo lorem non sem. Nam nec est ut tortor euismod tincidunt. Aenean facilisis tortor non velit. Ut nisl arcu, vestibulum id, posuere et, porttitor ac, magna. In volutpat, leo vel nonummy auctor, sem libero feugiat mauris, eu condimentum nibh sapien ac tortor. Proin ut augue. Sed laoreet, eros non ultrices dictum, lacus lacus lobortis justo, at molestie pede dolor sit amet ipsum. Integer nisl risus, laoreet sit amet, pretium quis, vulputate at, velit. Vivamus in nibh. Donec odio nisl, accumsan tempus, ullamcorper quis, facilisis a, arcu. Nulla varius. Nullam vel libero. Phasellus placerat, lacus et pellentesque semper, arcu dolor feugiat orci, vitae scelerisque dolor urna id libero. Maecenas vel purus. Vivamus mi justo, semper eu, tristique in, lacinia a, ante. Aenean et massa. Nulla gravida sem id nisi."""


if __name__ == '__main__':
    print lorem_ipsum(5)
    print
    print lorem_ipsum(5, 15)
    print
    print lorem_ipsum(1, sentences=True)
    print
    print lorem_ipsum(5, sentences=True)
    print
