#include <stdio.h>
#include <stack>
#include <string>
#include <sstream>

using namespace std;

string parser(const string& html_content) 
{
    stack<string> tags;
    stringstream result;
    bool in_tag = false;
    string current_tag;

    for (char c : html_content) 
    {
        if (c == '<') 
        {
            in_tag = true;
            current_tag.clear();
        }
        else if (c == '>') 
        {
            in_tag = false;
            if (!current_tag.empty() && current_tag[0] != '/') 
            {
                tags.push(current_tag);
                result << "Tag opened: " << current_tag << "\n";
            }
            else if (!current_tag.empty() && current_tag[0] == '/') 
            {
                if (!tags.empty() && tags.top() == current_tag.substr(1)) 
                {
                    result << "Tag closed: " << tags.top() << "\n";
                    tags.pop();
                }
                else 
                {
                    result << "Error: Mismatched closing tag " << current_tag << "\n";
                }
            }
        }
        else if (in_tag) 
        {
            current_tag += c;
        }
    }

    while (!tags.empty()) 
    {
        result << "Error: Unclosed tag " << tags.top() << "\n";
        tags.pop();
    }

    return result.str();
}
