/*
---
description: Masonry layout engine (converted from jQuery Masonry)

license: mooMasonry is dual-licensed under GPL and MIT, just like jQuery Masonry itself. You can use it for both personal and commercial applications.

authors:
- David DeSandro
- Olivier Refalo

requires:
- core/1.3.0:'*'

provides: [Element.masonry]
*/

var MasonryClass = new Class({

	options : {
		singleMode : false,
		columnWidth : undefined,
		itemSelector : undefined,
		appendedContent : undefined,
		resizeable : true
	},
	
	element : undefined,
	colW : undefined,
	colCount : undefined,
	lastColCount : undefined,
	colY : undefined,
	lastColY: undefined,
	bound : undefined,
	masoned : undefined,
	bricks : undefined,
	posLeft : undefined,
	brickParent : undefined,

	Implements : Options,

	initialize : function(element, options) {
		this.element = document.id(element);
		this.go(options);
	},
	
	go: function(options) {
		this.setOptions(options);
		
		if (this.masoned && options.appendedContent != undefined) {
			this.brickParent = options.appendedContent;
		} else {
			this.brickParent = this.element;
		}
		
		if (this.brickParent.getChildren().length > 0) {
			this.masonrySetup();
			this.masonryArrange();
		
			var resizeOn = this.options.resizeable;
				if (resizeOn) {
					if(this.bound == undefined) {
						this.bound = this.masonryResize.bind(this);
						this.attach();
					}
				}

				if (!resizeOn) {
					this.detach();
				}
		}
	},

	attach : function() {
		window.addEvent('resize', this.bound);
		return this;
	},

	detach : function() {
		if(this.bound != undefined ) {
			window.removeEvent('resize', this.bound);
			this.bound = undefined;
		}
		return this;
	},

	placeBrick : function(brick, setCount, setY, setSpan) {
		var shortCol = 0;
		
		for (var i = 0; i < setCount; i++) {
			if (setY[i] < setY[shortCol]) {
				shortCol = i;
			}
		}
		
		brick.setStyles({
			top : setY[shortCol],
			left : this.colW * shortCol + this.posLeft
		});
		
		var size=brick.getSize().y+brick.getStyle('margin-top').toInt()+brick.getStyle('margin-bottom').toInt();

		for (var i = 0; i < setSpan; i++) {
			this.colY[shortCol + i] = setY[shortCol] + size;
		}
	},

	masonrySetup : function() {
		var s = this.options.itemSelector;
		this.bricks = s == undefined ? this.brickParent.getChildren() : this.brickParent.getElements(s);
		
		if (this.options.columnWidth == undefined) {
			var b = this.bricks[0];
			this.colW = b.getSize().x + b.getStyle('margin-left').toInt() + b.getStyle('margin-right').toInt();
		} else {
			this.colW = this.options.columnWidth;
		}
		
		var size = this.element.getSize().x+this.element.getStyle('margin-left').toInt()+this.element.getStyle('margin-right').toInt();
		this.colCount = Math.floor(size / this.colW);
		this.colCount = Math.max(this.colCount, 1);
		
		return this;
	},

	masonryResize : function() {
		this.brickParent = this.element;
		this.lastColY=this.colY;
		this.lastColCount = this.colCount;
		
		this.masonrySetup();
		
		if (this.colCount != this.lastColCount) {
			this.masonryArrange();
		}
		return this;
	},

	masonryArrange : function() {
		// if masonry hasn't been called before
		if (!this.masoned) {
			this.element.setStyle('position', 'relative');
		}
		
		if (!this.masoned || this.options.appendedContent != undefined) {
			// just the new bricks
			this.bricks.setStyle('position', 'absolute');
		}
		
		// get top left position of where the bricks should be
		var cursor = new Element('div').inject(this.element, 'top');
		
		var pos = cursor.getPosition();
		var epos = this.element.getPosition();
		
		var posTop = pos.y - epos.y;
		this.posLeft = pos.x - epos.x;
		
		cursor.dispose();
		
		// set up column Y array
		if (this.masoned && this.options.appendedContent != undefined) {
			// if appendedContent is set, use colY from last call
			if(this.lastColY != undefined) {
				this.colY=this.lastColY; 
			}
		
			/*
			* in the case that the wall is not resizeable, but the colCount has
			* changed from the previous time masonry has been called
			*/
			for (var i = this.lastColCount; i < this.colCount; i++) {
				this.colY[i] = posTop;
			}
		
		} else {
			this.colY = [];
			for (var i = 0; i < this.colCount; i++) {
				this.colY[i] = posTop;
			}
		}
		
		// layout logic
		if (this.options.singleMode) {
			for (var k = 0; k < this.bricks.length; k++) {
				var brick = this.bricks[k];
				this.placeBrick(brick, this.colCount, this.colY, 1);
			}
		} else {
			for (var k = 0; k < this.bricks.length; k++) {
				var brick = this.bricks[k];
		
				// how many columns does this brick span
				var size=brick.getSize().x+brick.getStyle('margin-left').toInt()+brick.getStyle('margin-right').toInt();
				var colSpan = Math.ceil(size / this.colW);
				colSpan = Math.min(colSpan, this.colCount);
		
				if (colSpan == 1) {
					// if brick spans only one column, just like singleMode
					this.placeBrick(brick, this.colCount, this.colY, 1);
				} else {
					// brick spans more than one column
					// how many different places could this brick fit horizontally
					var groupCount = this.colCount + 1 - colSpan;
					var groupY = [0];
					// for each group potential horizontal position
					for (var i = 0; i < groupCount; i++) {
						groupY[i] = 0;
						// for each column in that group
						for (var j = 0; j < colSpan; j++) {
							// get the maximum column height in that group
							groupY[i] = Math.max(groupY[i], this.colY[i + j]);
						}
					}        					
					this.placeBrick(brick, groupCount, groupY, colSpan);
				} // else
			}
		} // /layout logic
		
		// set the height of the wall to the tallest column
		var wallH = 0;
		for (var i = 0; i < this.colCount; i++) {
			wallH = Math.max(wallH, this.colY[i]);
		}
		
		this.element.setStyle('height', wallH - posTop);
		
		// let listeners know that we are done
		this.element.fireEvent('masoned', this.element);
		this.masoned = true;
		this.options.appendedContent = undefined;
		
		// set all data so we can retrieve it for appended appendedContent
		// or anyone else's crazy jquery fun
		// this.element.data('masonry', props );
		return this;
	}

});

Element.implement({
	masonry : function(options) {
		new MasonryClass(this, options);
	}
});
