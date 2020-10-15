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
	/**
	 * The class returned from a call to connection.update(), contains information on the success of each updated requested
	 * 
	 * @tag Tag text
	 * @example 
	 * 
	 * @see http://www.salesforce.com/us/developer/docs/api/index.htm Apex Developer Doc
	 * 
	 * @author rhess @ salesforce.com, dcarroll @ saleforce.com, jaward @ adobe.com 
	 */	
	public dynamic class UpdatedResponse
	{	
		// in 8.0 we get ids array and a timestamp
		
		public function UpdatedResponse(obj:ObjectProxy) {
			var val:Object = obj[key];
			for (var key:String in obj) {
				if (val is ArrayCollection || val is ObjectProxy) { 
					this[key] = new Array();
					if (val is ObjectProxy) {
						this[key].push( val) ;
					} else {
						for (var i:int = 0; i<(val as ArrayCollection).length;i++) { 
							this[key].push( (val as Array)[i] );
						}
					}
		
				} else {
					this[key] = obj[key];
				}
			}
		}		
	}
}