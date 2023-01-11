# utils.py

from typing import Dict, List


def list_to_element_counted_and_sorted_dict(my_raw_list: List[str]) -> Dict:
    '''
      Takes a list of element, counts each element and
      return a dict of key = element, value = number of occurence,
      sorted from greater occcurences to lower
    '''
    my_counted_list = {
        element: my_raw_list.count(element)
        for element in my_raw_list
    }
    my_ordered_dict = {
        key: value
        for key, value in sorted(
            my_counted_list.items(),
            key=lambda item: item[1],
            reverse=True
        )
    }
    return my_ordered_dict
