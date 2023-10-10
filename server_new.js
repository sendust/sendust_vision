const  express = require('express');
const  app = express();
const  http = require('http').Server(app);
const  io = require('socket.io')(http);
const  serveIndex = require('serve-index')

const cloudcmd = require('cloudcmd');
const fm_server = require('socket.io').Server;


const port = 3000;
const prefix = '/fm';

//const server = require('http').createServer(app);

const fm_socket = new fm_server(http, {
    path: `${prefix}socket.io`,
});


app.use(prefix, cloudcmd({
    socket: fm_socket,
    config : {'name': 'sendust_filemanager',
              'root': '\\',
              'one-panel-mode': true,}
}));


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


app.use((req, res, next) => {
    res.status(404).send(
        "<h1>Page not found on the server</h1>")
})



http.listen(port, function(){
   // console.log('listening on localhost:3000');
	updatelog(`listening on localhost:${port}`);
});

setTimeout(()=>{console.log(`listening on localhost:${port}`)}, 2000)

function updatelog(text){
    now = new Date().toISOString();
    console.log(now + " " + text);
}