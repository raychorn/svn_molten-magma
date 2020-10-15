/*
Copyright (c) 2007 salesforce.com, inc.
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions
are met:

1. Redistributions of source code must retain the above copyright
   notice, this list of conditions and the following disclaimer.
2. Redistributions in binary form must reproduce the above copyright
   notice, this list of conditions and the following disclaimer in the
   documentation and/or other materials provided with the distribution.
3. The name of the author may not be used to endorse or promote products
   derived from this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE AUTHOR "AS IS" AND ANY EXPRESS OR
IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES
OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED.
IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR ANY DIRECT, INDIRECT,
INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT
NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF
THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
*/
package com.salesforce.results
{
	import mx.utils.ObjectProxy;
	import mx.collections.ArrayCollection;
	
	public dynamic class DeletedResponse
	{
		public var earliestDateAvailable:String;
		public var latestDateCovered:String
		public var deletedRecords:ArrayCollection;
		
		// TODO this changes in 9.0
		public function DeletedResponse(obj:ObjectProxy) {
			this.latestDateCovered  = obj.latestDateCovered;
			this.earliestDateAvailable = obj.earliestDateAvailable;
			this.deletedRecords = new ArrayCollection();
			if ( obj.deletedRecords && obj.deletedRecords.length > 0 ) {  // perhaps none were found 
				for( var i:int = 0; i < obj.deletedRecords.length; i++) {
					this.deletedRecords.addItem( new DeletedRecord( obj.deletedRecords[i]));
				}	
			}
		}
	}
}