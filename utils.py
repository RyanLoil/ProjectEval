from selenium.webdriver.common.by import By


def selenium_find_minimum_ancestor(driver, source_tag, check_by, check_text):
    counter = 5
    tag = source_tag
    while counter > 0:
        try:
            tag.find_element(check_by, check_text)
            break
        except Exception:
            tag = tag.find_element(By.XPATH, "./ancestor::*[1]")
            counter -= 1
            continue
    if counter == 0:
        raise AssertionError('No minimum ancestor found')
    return tag