# coding: utf-8
from django.utils.safestring import mark_safe


class pagehelper(object):  # 分页类
    def __init__(self, current, totalitems, peritems=10):  # 传三个参数，当前页，总记录数，每页条数
        self.current = current
        self.totalitems = totalitems
        self.peritems = peritems

    def prev(self):  # 一页数据ID起始
        return int(int(self.current) - 1) * int(self.peritems)

    def next1(self):  # 一页数据ID结束
        return int(self.current) * int(self.peritems)

    def totalpage(self):  # 总页数
        page = divmod(int(self.totalitems), int(self.peritems))
        if page[1] == 0:
            return page[0]
        else:
            return page[0] + 1


def generatehtml(baseurl, currentpage, totalpage):  # 基础页，当前页，总页数
    perpager = 11  # 最多显示页码
    begin = 0  # 起始
    end = 0  # 结束
    if totalpage <= 11:     # 总共显示11个页码
        begin = 0
        end = totalpage
    else:
        if currentpage > 5:
            begin = currentpage - 6
            end = currentpage + 5
            if end > totalpage:
                end = totalpage
        else:
            begin = 0
            end = 11
    pager_list = []
    if currentpage <= 1:
        first = "<a class='page' href='%s%d'  title='首页'>首页</a>" % (baseurl, 1)  # /user/list/?page= 这种格式
        first = '<li class ="paginate_button previous  active" aria-controls="editable" tabindex="0" id="editable_previous">' + first + '</li>'
    else:
        first = "<a class='page' href='%s%d'  title='首页'>首页</a>" % (baseurl, 1)  # /user/list/?page= 这种格式
        first = '<li class ="paginate_button previous  active" aria-controls="editable" tabindex="0" id="editable_previous">' + first + '</li>'
    pager_list.append(first)

    if currentpage <= 1:
        prev = "<a class='page' href='%s%d'  title='首页'>上一页</a>" % (baseurl, 1)
        prev = '<li class="paginate_button active"  aria-controls="editable" tabindex="0">' + prev + '</li>'
    else:
        prev = "<a class='page' href='%s%d'  title='上一页'>上一页</a>" % (baseurl, currentpage - 1)
        prev = '<li class="paginate_button active"  aria-controls="editable" tabindex="0">' + prev + '</li>'
    pager_list.append(prev)

    for i in range(begin + 1, end + 1):
        if i == currentpage:
            temp = "<a class='page' href='%s%d'  title='%d''>%d</a>" % (baseurl, i, i, i)  # 如果需要当前页显示特别就设这个
            temp = '<li class="paginate_button active"  aria-controls="editable" tabindex="0">' + temp + '</li>'
        else:
            temp = "<a class='page' href='%s%d'  title='%d'>%d</a>" % (baseurl, i, i, i)
            temp = '<li class="paginate_button" aria-controls="editable" tabindex="0">' + temp + '</li>'
        pager_list.append(temp)
    if currentpage >= totalpage:
        next = "<a class='page' href='#'  title='下一页'>下一页</a>"
        next = '<li class="paginate_button active"  aria-controls="editable" tabindex="0">' + next + '</li>'
    else:
        next = "<a class='page' href='%s%d'  title='下一页'>下一页</a>" % (baseurl, currentpage + 1)
        next = '<li class="paginate_button active"  aria-controls="editable" tabindex="0">' + next + '</li>'
    pager_list.append(next)
    if currentpage >= totalpage:
        last = "<a class='page' href='#'>末页</a>"
        last = '<li class="paginate_button next  active" aria-controls="editable" tabindex="0" id="editable_next">' + last + '</li>'
    else:
        last = "<a class='page' href='%s%d'>末页</a>" % (baseurl, totalpage)
        last = '<li class="paginate_button next  active" aria-controls="editable" tabindex="0" id="editable_next">' + last + '</li>'
    pager_list.append(last)
    result = ''.join(pager_list)
    return mark_safe(result)  # 把字符串转成html语言
