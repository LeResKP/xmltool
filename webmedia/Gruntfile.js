'use strict';

module.exports = function(grunt) {

  // Project configuration.
  grunt.initConfig({
    // Metadata.
    pkg: grunt.file.readJSON('xmltool.jquery.json'),
    banner: '/*! <%= pkg.title || pkg.name %> - v<%= pkg.version %> - ' +
      '<%= grunt.template.today("yyyy-mm-dd") %>\n' +
      '<%= pkg.homepage ? "* " + pkg.homepage + "\\n" : "" %>' +
      '* Copyright (c) <%= grunt.template.today("yyyy") %> <%= pkg.author.name %>;' +
      ' Licensed <%= _.pluck(pkg.licenses, "type").join(", ") %> */\n',

    // Task configuration.
    clean: {
      files: ['dist']
    },
    concat: {
      options: {
        banner: '<%= banner %>',
        stripBanners: true
      },
      dist: {
        src: ['js/*.js'],
        dest: 'dist/js/<%= pkg.name %>.js'
      },
    },
    uglify: {
      options: {
        banner: '<%= banner %>'
      },
      dist: {
        src: '<%= concat.dist.dest %>',
        dest: 'dist/js/<%= pkg.name %>.min.js'
      },
    },
    qunit: {
        options: {
          '--local-to-remote-url-access': true
          },
        files: ['js/test/xmltool.html']
    },
    jshint: {
      gruntfile: {
        options: {
          jshintrc: '.jshintrc'
        },
        src: 'Gruntfile.js'
      },
      src: {
        options: {
          jshintrc: 'js/.jshintrc'
        },
        src: ['js/**/*.js']
      },
      test: {
        options: {
          jshintrc: 'js/test/.jshintrc'
        },
        src: ['js/test/**/*.js']
      },
    },
    less: {
        development: {
            options: {
                paths: ['bower_components/bootstrap/less/']
            },
            files: {
                "dist/css/<%= pkg.name %>.css": "css/xmltool.less"
            }
        },
        production: {
            options: {
                paths: ['bower_components/bootstrap/less/'],
                cleancss: true
            },
            files: {
                "dist/css/<%= pkg.name %>.min.css": "css/xmltool.less"
            }
        }
    },
    copy: {
        main: {
            files: [
                {
                    expand: true,
                    cwd: 'libs/bootstrap-3.0.2/fonts',
                    src: ['*'],
                    dest: 'dist/fonts/'
                }
            ]
        }
    },
    watch: {
      gruntfile: {
        files: '<%= jshint.gruntfile.src %>',
        tasks: ['jshint:gruntfile']
      },
      src: {
        files: '<%= jshint.src.src %>',
        tasks: ['jshint:src', 'qunit']
      },
      test: {
        files: '<%= jshint.test.src %>',
        tasks: ['jshint:test', 'qunit']
      },
    },
    connect: {
      server: {
        options: {
          hostname: 'localhost',
          port: 9999,
          middleware: function(connect, options, middleware) {
            var lis = [
                function(req, res, next) {
                    res.setHeader('Access-Control-Allow-Origin', '*');
                    res.setHeader('Access-Control-Allow-Methods', '*');
                    next();
                }
            ];
            return lis.concat(middleware);
          }
        }
      }
    },
    jsdoc : {
        dist : {
            src: ['js/*.js'],
            options: {
                destination: 'doc',
                configure: '.jsdoc.json'
            },
            // Use last version of jsdoc to have better markdown support
            jsdoc: 'node_modules/.bin/jsdoc'
        },
    }
  });

  require('load-grunt-tasks')(grunt, {scope: 'devDependencies'});
  require('time-grunt')(grunt);

  // Default task.
  grunt.registerTask('default', ['jshint', 'qunit', 'clean', 'concat', 'uglify', 'less', 'copy']);
  grunt.registerTask('dev', ['connect', 'watch']);
  grunt.registerTask('test', ['connect', 'qunit']);
  grunt.registerTask('doc', ['jsdoc']);

};
