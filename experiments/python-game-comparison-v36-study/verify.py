"""Check the retained native comparison, without rerunning encoders."""
from compare import main
import sys
if __name__=='__main__':
    sys.argv=['compare.py','--check'];main()
