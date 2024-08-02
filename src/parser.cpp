#include <stdio.h>
#include<stack>
#include<string>
#include<queue>

using namespace std;

std::string parser(std::string html_content) 
{
    int i = 0;
    stack<std::string> elem_end;
    queue<std::string> elem_start;
    bool is_elem;
    stack<std::string> tag_end;
    queue<std::string> tag_start;
    bool is_tag;
    char current;    
    while(i<=html_content.size())
    {
        current = html_content[0];
        if(current == '<') 
        {
            tag_start.push(current);
            is_tag = true;

        }
        else if(current == '>')
        {
            tag_end.push(current);
            is_tag = false;
        }
    } 
}