~/wsdl/README.txt

The files in this directory are for generating the python
proxy classes used as a base for this API.

Run the python file sfGenBase.py (using ge as model).

Download a new version of the partner.wsdl from sForce after
you verify that the included file works as you expect.

sfGenBase.py will create the two service proxy files in the
subdirectory generated.  

   SforceService_services.py       - Classes for each API call
   SforceService_services_types.py - Classes for message types used by above

The subdirectory gen_part is a working set of class proxy files.
Compare the files in generated to the files in gen_part to see any
differences.

ZSI version 1.5.1 is expected to be in your python path.