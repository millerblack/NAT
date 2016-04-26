import sys


def outputname(base_name):
    print ''.join([x.capitalize() for x in base_name.split('-')])


if __name__ == '__main__':
    outputname(sys.argv[1])
