var express = require('express');
var app = express();
var http = require('http').Server(app);
var io = require('socket.io')(http);
var serveIndex = require('serve-index')



app.get('/', function(req, res){
        res.sendFile(__dirname + '/client_gui.html');
});

app.use('/log', express.static('log'), serveIndex('log', {'icons': true}))
app.use('/image', express.static('image'), serveIndex('image', {'icons': true}))

io.on('connection', function(socket){
   // console.log('A user connected');
   updatelog('A user connected');
   
   // Send a message when
   socket.on('disconnect', function () {
        // console.log('A user disconnected');
        updatelog('A user disconnected');
   });
   socket.on('msg_engine', (data)=>{
        socket.broadcast.emit("msg_engine_status", data);
        // console.log(data);
        updatelog("[msg_engine] ---> [msg_engine_status]");
    });

   socket.on('msg_gui', (data)=>{
        socket.broadcast.emit("msg_gui", data);
        console.log(data);
        updatelog("[msg_gui] <--- [msg_gui]");
    });


});



http.listen(3000, function(){
   // console.log('listening on localhost:3000');
   updatelog('listening on localhost:3000');
});


function updatelog(text){
    now = new Date().toISOString();
    console.log(now + " " + text);
}